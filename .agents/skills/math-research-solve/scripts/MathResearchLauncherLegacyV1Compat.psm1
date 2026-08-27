Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$script:PromptHeader = '# Math Research Orchestration Prompt v6'
$script:LegacyPromptHeader = '# Math Research Orchestration Prompt v3'
$script:ManifestFileName = 'run.json'
$script:AllowedSignerNames = @('OpenAI OpCo, LLC', 'OpenAI, L.L.C.')
$script:HeldMutexNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$script:ManifestKeyPathOverrideForTests = $null
$script:ReservedRunNames = @(
    'run.json',
    'run.json.bak',
    '.launcher.lease',
    'goal-bootstrap.md',
    'goal-output-schema.json',
    'research-turn.md',
    'cycle-policy.json',
    'cycle-tickets-000.json',
    'stop-request.json',
    'stop-request.json.bak'
)

if (-not ('MathResearchLauncher.ManagedProcess' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace MathResearchLauncher
{
    [StructLayout(LayoutKind.Sequential)]
    internal struct IO_COUNTERS
    {
        public UInt64 ReadOperationCount;
        public UInt64 WriteOperationCount;
        public UInt64 OtherOperationCount;
        public UInt64 ReadTransferCount;
        public UInt64 WriteTransferCount;
        public UInt64 OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public Int64 PerProcessUserTimeLimit;
        public Int64 PerJobUserTimeLimit;
        public UInt32 LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public UInt32 ActiveProcessLimit;
        public Int64 Affinity;
        public UInt32 PriorityClass;
        public UInt32 SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    public sealed class ManagedProcessResult
    {
        public int ProcessId { get; internal set; }
        public int ExitCode { get; internal set; }
        public bool TimedOut { get; internal set; }
        public bool OutputLimitExceeded { get; internal set; }
        public bool StandardInputFailed { get; internal set; }
        public string StandardInputError { get; internal set; }
        public string ProcessStartTimeUtc { get; internal set; }
        public string ProcessEndTimeUtc { get; internal set; }
    }

    public sealed class ManagedProcess : IDisposable
    {
        private const UInt32 JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;
        private const UInt32 JOB_OBJECT_TERMINATE = 0x0008;
        private const int JobObjectExtendedLimitInformation = 9;
        private const int ERROR_ALREADY_EXISTS = 183;

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr CreateJobObjectW(IntPtr lpJobAttributes, string lpName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetInformationJobObject(
            IntPtr hJob,
            int JobObjectInfoClass,
            IntPtr lpJobObjectInfo,
            UInt32 cbJobObjectInfoLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr OpenJobObjectW(UInt32 dwDesiredAccess, bool bInheritHandle, string lpName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool TerminateJobObject(IntPtr hJob, UInt32 uExitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr hObject);

        private readonly Process process;
        private readonly FileStream stdoutFile;
        private readonly FileStream stderrFile;
        private readonly Task stdinWrite;
        private readonly Task stdoutCopy;
        private readonly Task stderrCopy;
        private IntPtr jobHandle;
        private bool disposed;
        private bool waited;

        public int ProcessId { get { return process.Id; } }
        public string ProcessStartTimeUtc { get; private set; }
        public bool JobAssigned { get; private set; }
        public string JobName { get; private set; }

        private void TerminateTree(UInt32 exitCode)
        {
            bool terminated = jobHandle != IntPtr.Zero && TerminateJobObject(jobHandle, exitCode);
            if (!terminated)
            {
                try { process.Kill(true); }
                catch { }
            }
        }

        private ManagedProcess(
            Process process,
            FileStream stdoutFile,
            FileStream stderrFile,
            Task stdinWrite,
            Task stdoutCopy,
            Task stderrCopy,
            IntPtr jobHandle,
            string jobName)
        {
            this.process = process;
            this.stdoutFile = stdoutFile;
            this.stderrFile = stderrFile;
            this.stdinWrite = stdinWrite;
            this.stdoutCopy = stdoutCopy;
            this.stderrCopy = stderrCopy;
            this.jobHandle = jobHandle;
            this.ProcessStartTimeUtc = process.StartTime.ToUniversalTime().ToString("O");
            this.JobAssigned = true;
            this.JobName = jobName;
        }

        private static async Task WriteStandardInputAsync(StreamWriter writer, string standardInput)
        {
            try
            {
                if (!String.IsNullOrEmpty(standardInput))
                {
                    await writer.WriteAsync(standardInput).ConfigureAwait(false);
                    await writer.FlushAsync().ConfigureAwait(false);
                }
            }
            finally
            {
                writer.Dispose();
            }
        }

        public static ManagedProcess Start(
            string executable,
            IList<string> arguments,
            string workingDirectory,
            string standardInput,
            string stdoutPath,
            string stderrPath,
            IDictionary<string, string> environment,
            string jobName)
        {
            FileStream stdoutFile = null;
            FileStream stderrFile = null;
            Process process = null;
            IntPtr job = IntPtr.Zero;
            try
            {
                stdoutFile = new FileStream(stdoutPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read, 65536, FileOptions.SequentialScan);
                stderrFile = new FileStream(stderrPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read, 65536, FileOptions.SequentialScan);

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = executable;
                psi.WorkingDirectory = workingDirectory;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.RedirectStandardInput = true;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;
                psi.StandardInputEncoding = new UTF8Encoding(false, true);
                psi.StandardOutputEncoding = new UTF8Encoding(false, true);
                psi.StandardErrorEncoding = new UTF8Encoding(false, true);
                foreach (string argument in arguments)
                {
                    psi.ArgumentList.Add(argument);
                }
                if (environment != null)
                {
                    psi.Environment.Clear();
                    foreach (KeyValuePair<string, string> item in environment)
                    {
                        psi.Environment[item.Key] = item.Value;
                    }
                }

                job = CreateJobObjectW(IntPtr.Zero, jobName);
                if (job == IntPtr.Zero)
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateJobObjectW failed");
                }
                if (!String.IsNullOrEmpty(jobName) && Marshal.GetLastWin32Error() == ERROR_ALREADY_EXISTS)
                {
                    throw new InvalidOperationException("The requested Job Object name already exists");
                }

                JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
                info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                int length = Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
                IntPtr infoPtr = Marshal.AllocHGlobal(length);
                try
                {
                    Marshal.StructureToPtr(info, infoPtr, false);
                    if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, infoPtr, (UInt32)length))
                    {
                        throw new Win32Exception(Marshal.GetLastWin32Error(), "SetInformationJobObject failed");
                    }
                }
                finally
                {
                    Marshal.FreeHGlobal(infoPtr);
                }

                process = new Process();
                process.StartInfo = psi;
                if (!process.Start())
                {
                    throw new InvalidOperationException("Process.Start returned false");
                }
                if (!AssignProcessToJobObject(job, process.Handle))
                {
                    int error = Marshal.GetLastWin32Error();
                    try { process.Kill(true); } catch { }
                    throw new Win32Exception(error, "AssignProcessToJobObject failed");
                }

                Task stdoutCopy = process.StandardOutput.BaseStream.CopyToAsync(stdoutFile);
                Task stderrCopy = process.StandardError.BaseStream.CopyToAsync(stderrFile);
                Task stdinWrite = WriteStandardInputAsync(process.StandardInput, standardInput);

                return new ManagedProcess(process, stdoutFile, stderrFile, stdinWrite, stdoutCopy, stderrCopy, job, jobName);
            }
            catch
            {
                if (process != null)
                {
                    try { if (!process.HasExited) process.Kill(true); } catch { }
                    process.Dispose();
                }
                if (job != IntPtr.Zero) CloseHandle(job);
                if (stdoutFile != null) stdoutFile.Dispose();
                if (stderrFile != null) stderrFile.Dispose();
                throw;
            }
        }

        public static void TerminateNamedJob(string jobName, UInt32 exitCode)
        {
            if (String.IsNullOrWhiteSpace(jobName)) throw new ArgumentException("Job Object name is required", "jobName");
            IntPtr job = OpenJobObjectW(JOB_OBJECT_TERMINATE, false, jobName);
            if (job == IntPtr.Zero)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "OpenJobObjectW failed");
            }
            try
            {
                if (!TerminateJobObject(job, exitCode))
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "TerminateJobObject failed");
                }
            }
            finally { CloseHandle(job); }
        }

        public ManagedProcessResult Wait(long timeoutMilliseconds, long maxStdoutBytes, long maxStderrBytes)
        {
            if (disposed) throw new ObjectDisposedException("ManagedProcess");
            if (waited) throw new InvalidOperationException("Wait may only be called once");
            waited = true;

            Stopwatch stopwatch = Stopwatch.StartNew();
            bool timedOut = false;
            bool outputLimitExceeded = false;

            while (!process.HasExited)
            {
                if (maxStdoutBytes > 0 && stdoutFile.Length > maxStdoutBytes)
                {
                    outputLimitExceeded = true;
                    TerminateTree(137);
                    break;
                }
                if (maxStderrBytes > 0 && stderrFile.Length > maxStderrBytes)
                {
                    outputLimitExceeded = true;
                    TerminateTree(137);
                    break;
                }
                if (timeoutMilliseconds > 0 && stopwatch.ElapsedMilliseconds >= timeoutMilliseconds)
                {
                    timedOut = true;
                    TerminateTree(124);
                    break;
                }
                Thread.Sleep(200);
            }

            if (!process.WaitForExit(15000))
            {
                TerminateTree(137);
                if (!process.WaitForExit(15000))
                {
                    throw new TimeoutException("The managed process did not exit after two bounded termination attempts.");
                }
            }

            Exception stdinError = null;
            try { stdinWrite.GetAwaiter().GetResult(); }
            catch (Exception ex) { stdinError = ex; }
            Task.WhenAll(stdoutCopy, stderrCopy).GetAwaiter().GetResult();
            if ((maxStdoutBytes > 0 && stdoutFile.Length > maxStdoutBytes) ||
                (maxStderrBytes > 0 && stderrFile.Length > maxStderrBytes))
            {
                outputLimitExceeded = true;
            }
            stdoutFile.Flush(true);
            stderrFile.Flush(true);

            return new ManagedProcessResult
            {
                ProcessId = process.Id,
                ExitCode = process.ExitCode,
                TimedOut = timedOut,
                OutputLimitExceeded = outputLimitExceeded,
                StandardInputFailed = stdinError != null,
                StandardInputError = stdinError == null ? null : stdinError.GetBaseException().Message,
                ProcessStartTimeUtc = ProcessStartTimeUtc,
                ProcessEndTimeUtc = DateTime.UtcNow.ToString("O")
            };
        }

        public void Dispose()
        {
            if (disposed) return;
            disposed = true;
            try
            {
                if (!process.HasExited)
                {
                    TerminateTree(137);
                    process.WaitForExit(15000);
                }
            }
            catch { }
            try { stdinWrite.GetAwaiter().GetResult(); } catch { }
            try { Task.WhenAll(stdoutCopy, stderrCopy).GetAwaiter().GetResult(); } catch { }
            stdoutFile.Dispose();
            stderrFile.Dispose();
            process.Dispose();
            if (jobHandle != IntPtr.Zero)
            {
                CloseHandle(jobHandle);
                jobHandle = IntPtr.Zero;
            }
        }
    }
}
'@
}

function Assert-PowerShell7 {
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        throw 'The math research launcher requires PowerShell 7 or later.'
    }
    if (-not $IsWindows) {
        throw 'The bundled launcher currently supports Windows only.'
    }
}

function Get-UtcNowString {
    return [DateTime]::UtcNow.ToString('O')
}

function Get-Sha256HexFromBytes {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $hash = [Security.Cryptography.SHA256]::HashData($Bytes)
    return [Convert]::ToHexString($hash).ToLowerInvariant()
}

function Get-Sha256HexFromText {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)
    return Get-Sha256HexFromBytes -Bytes ([Text.UTF8Encoding]::new($false).GetBytes($Text))
}

function Get-Sha256HexFromFile {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}

function Test-FixedTimeHexEqual {
    param(
        [Parameter(Mandatory = $true)][string]$Left,
        [Parameter(Mandatory = $true)][string]$Right
    )
    try {
        $a = [Convert]::FromHexString($Left)
        $b = [Convert]::FromHexString($Right)
    }
    catch {
        return $false
    }
    if ($a.Length -ne $b.Length) { return $false }
    return [Security.Cryptography.CryptographicOperations]::FixedTimeEquals($a, $b)
}

function Assert-LocalAbsolutePath {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    if ([string]::IsNullOrWhiteSpace($LiteralPath)) { throw 'Path cannot be empty.' }
    if (-not [IO.Path]::IsPathFullyQualified($LiteralPath)) {
        throw "Path must be absolute: $LiteralPath"
    }
    if ($LiteralPath.StartsWith('\\', [StringComparison]::Ordinal) -or
        $LiteralPath.StartsWith('\\?\', [StringComparison]::Ordinal) -or
        $LiteralPath.StartsWith('\\.\', [StringComparison]::Ordinal)) {
        throw "UNC and device paths are not allowed: $LiteralPath"
    }
    $full = [IO.Path]::GetFullPath($LiteralPath)
    $root = [IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrWhiteSpace($root) -or $root.StartsWith('\\')) {
        throw "Only local drive paths are allowed: $LiteralPath"
    }
    return $full.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Assert-NoReparsePointChain {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $full = Assert-LocalAbsolutePath -LiteralPath $LiteralPath
    $root = [IO.Path]::GetPathRoot($full).TrimEnd('\')
    $relative = $full.Substring([IO.Path]::GetPathRoot($full).Length)
    $current = if ($root) { "$root\" } else { [IO.Path]::GetPathRoot($full) }
    foreach ($part in ($relative -split '[\\/]' | Where-Object { $_ -ne '' })) {
        $current = Join-Path $current $part
        if (-not (Test-Path -LiteralPath $current)) { break }
        $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not allowed in trusted paths: $($item.FullName)"
        }
    }
    return $full
}

function Test-PathInsideDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Child,
        [Parameter(Mandatory = $true)][string]$Directory
    )
    $childFull = [IO.Path]::GetFullPath($Child)
    $directoryFull = [IO.Path]::GetFullPath($Directory).TrimEnd('\') + '\'
    return $childFull.StartsWith($directoryFull, [StringComparison]::OrdinalIgnoreCase)
}

function Get-ResearchRunsRoot {
    if ([string]::IsNullOrWhiteSpace($env:OBSIDIAN_VAULT_ROOT)) {
        throw 'OBSIDIAN_VAULT_ROOT is required for the bounded-write math research launcher.'
    }
    $vaultRoot = Assert-LocalAbsolutePath -LiteralPath $env:OBSIDIAN_VAULT_ROOT
    return [IO.Path]::GetFullPath((Join-Path $vaultRoot '笔记草稿\数学研究运行')).TrimEnd('\')
}

function Get-ResearchProjectsRoot {
    if ([string]::IsNullOrWhiteSpace($env:OBSIDIAN_VAULT_ROOT)) {
        throw 'OBSIDIAN_VAULT_ROOT is required for the bounded-write math research launcher.'
    }
    $vaultRoot = Assert-LocalAbsolutePath -LiteralPath $env:OBSIDIAN_VAULT_ROOT
    return [IO.Path]::GetFullPath((Join-Path $vaultRoot '笔记草稿\公开问题的尝试')).TrimEnd('\')
}

function Resolve-ResearchRunContext {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][ValidateSet('New','Resume','Control')][string]$Operation
    )
    $runPath = Assert-NoReparsePointChain -LiteralPath $RunDirectory
    $item = Get-Item -LiteralPath $runPath -Force -ErrorAction Stop
    if (-not $item.PSIsContainer) { throw "RunDirectory must be a directory: $runPath" }
    $runId = Split-Path -Leaf $runPath
    if ($runId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$' -or $runId.EndsWith('.') -or $runId.EndsWith(' ')) { throw "Unsafe run id: $runId" }

    $legacyRoot = Get-ResearchRunsRoot
    if ((Split-Path -Parent $runPath).Equals($legacyRoot, [StringComparison]::OrdinalIgnoreCase)) {
        if ($Operation -eq 'New') { throw 'New runs are forbidden in the legacy math research runs root; create them under an approved project archive runs directory.' }
        Assert-NoReparsePointChain -LiteralPath $legacyRoot | Out-Null
        return [pscustomobject]@{ RunPath=$runPath; Layout='legacy'; ProjectDirectory=$null; ProjectId=$null; ProjectDirectoryName=$null; ProjectArchiveSchema=$null }
    }

    $runsDirectory = Split-Path -Parent $runPath
    $projectDirectory = Split-Path -Parent $runsDirectory
    $projectsRoot = Get-ResearchProjectsRoot
    if ((Split-Path -Leaf $runsDirectory) -cne 'runs' -or -not (Split-Path -Parent $projectDirectory).Equals($projectsRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'RunDirectory must be a direct child of <approved-project>\runs, or a legacy direct child for Resume/Control.'
    }
    if (-not (Test-Path -LiteralPath $projectsRoot -PathType Container)) { throw "The approved math research projects root does not exist: $projectsRoot" }
    Assert-NoReparsePointChain -LiteralPath $projectsRoot | Out-Null
    $projectModule = Join-Path $PSScriptRoot 'MathResearchProjectArchive.psm1'
    if ($null -eq (Get-Command Resolve-MathResearchProjectDirectory -ErrorAction SilentlyContinue) -or $null -eq (Get-Command Verify-MathResearchProjectArchive -ErrorAction SilentlyContinue)) { Import-Module $projectModule -DisableNameChecking }
    Verify-MathResearchProjectArchive -ProjectDirectory $projectDirectory | Out-Null
    $project = Resolve-MathResearchProjectDirectory -ProjectDirectory $projectDirectory
    if (-not $runsDirectory.Equals((Join-Path $project.Path 'runs'), [StringComparison]::OrdinalIgnoreCase)) { throw 'RunDirectory is not in the project runs directory.' }
    return [pscustomobject]@{ RunPath=$runPath; Layout='project'; ProjectDirectory=$project.Path; ProjectId=[string]$project.Project.project_id; ProjectDirectoryName=$project.Name; ProjectArchiveSchema=[int]$project.Project.schema }
}

function Resolve-ResearchRunDirectory {
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    return (Resolve-ResearchRunContext -RunDirectory $RunDirectory -Operation Control).RunPath
}

function Resolve-RunInputFile {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $path = Assert-NoReparsePointChain -LiteralPath $LiteralPath
    $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    if ($item.PSIsContainer) { throw "$Label must be a file: $path" }
    if (-not (Split-Path -Parent $path).Equals($RunDirectory, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label must be a direct child of RunDirectory: $path"
    }
    if ($item.Extension -notin @('.md', '.txt')) {
        throw "$Label must use a .md or .txt extension: $path"
    }
    if ($script:ReservedRunNames -contains $item.Name -or
        $item.Name -match '^(events|stderr|last-message)-\d{3}-' -or
        $item.Name -match '^continuation-turn-\d{3}\.md$') {
        throw "$Label uses a reserved launcher file name: $($item.Name)"
    }
    return $path
}

function Assert-FreshRunDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string[]]$AllowedInputFiles
    )
    $allowed = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($file in $AllowedInputFiles) { [void]$allowed.Add([IO.Path]::GetFullPath($file)) }

    foreach ($item in (Get-ChildItem -LiteralPath $RunDirectory -Force -ErrorAction Stop)) {
        if ($item.PSIsContainer) {
            throw "A new run directory cannot contain subdirectories: $($item.FullName)"
        }
        if (-not $allowed.Contains($item.FullName)) {
            throw "A new run directory may contain only the approved prompt and goal objective files: $($item.FullName)"
        }
    }
    if (Test-Path -LiteralPath (Join-Path $RunDirectory $script:ManifestFileName)) {
        throw "RunDirectory already contains a manifest: $RunDirectory"
    }
}

function Read-StrictUtf8File {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][long]$MaximumBytes,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $bytes = [IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -eq 0) { throw "$Label is empty: $LiteralPath" }
    if ($bytes.Length -gt $MaximumBytes) {
        throw "$Label exceeds the $MaximumBytes-byte limit: $LiteralPath"
    }
    $offset = 0
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $offset = 3
    }
    try {
        $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes, $offset, $bytes.Length - $offset)
    }
    catch {
        throw "$Label is not valid UTF-8: $LiteralPath"
    }
    if ([string]::IsNullOrWhiteSpace($text)) { throw "$Label contains no text: $LiteralPath" }
    return [pscustomobject]@{
        Text = $text
        Bytes = $bytes.Length
        Sha256 = Get-Sha256HexFromBytes -Bytes $bytes
    }
}

function Write-Utf8FileNew {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text
    )
    $parent = Split-Path -Parent $LiteralPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw "Output parent does not exist: $parent"
    }
    $encoding = [Text.UTF8Encoding]::new($false)
    $stream = [IO.FileStream]::new($LiteralPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try {
        $bytes = $encoding.GetBytes($Text)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
}

function ConvertTo-CanonicalJson {
    param([Parameter(Mandatory = $true)]$InputObject)
    return ($InputObject | ConvertTo-Json -Depth 64 -Compress)
}

function Get-ManifestKeyPath {
    if (-not [string]::IsNullOrWhiteSpace($script:ManifestKeyPathOverrideForTests)) {
        return [IO.Path]::GetFullPath($script:ManifestKeyPathOverrideForTests)
    }
    return Join-Path (Get-TrustedLocalAppData) 'OpenAI\Codex\MathResearchLauncher\manifest-key.dpapi'
}

function Get-ManifestKey {
    param([switch]$CreateIfMissing)
    $path = Get-ManifestKeyPath
    $parent = Split-Path -Parent $path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        if (-not $CreateIfMissing) { throw "Manifest key directory is missing: $parent" }
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Assert-NoReparsePointChain -LiteralPath $parent | Out-Null

    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        if (-not $CreateIfMissing) { throw "Manifest key is missing: $path" }
        $plain = [byte[]]::new(32)
        [Security.Cryptography.RandomNumberGenerator]::Fill($plain)
        try {
            $protected = [Security.Cryptography.ProtectedData]::Protect(
                $plain,
                $null,
                [Security.Cryptography.DataProtectionScope]::CurrentUser)
            $temp = "$path.tmp.$([Guid]::NewGuid().ToString('N'))"
            $stream = [IO.FileStream]::new($temp, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try {
                $stream.Write($protected, 0, $protected.Length)
                $stream.Flush($true)
            }
            finally { $stream.Dispose() }
            try { [IO.File]::Move($temp, $path) }
            catch {
                if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
                if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw }
            }
        }
        finally { [Array]::Clear($plain, 0, $plain.Length) }
    }

    Assert-NoReparsePointChain -LiteralPath $path | Out-Null
    $protectedBytes = [IO.File]::ReadAllBytes($path)
    try {
        return [Security.Cryptography.ProtectedData]::Unprotect(
            $protectedBytes,
            $null,
            [Security.Cryptography.DataProtectionScope]::CurrentUser)
    }
    catch {
        throw "Manifest key cannot be decrypted for the current Windows user: $path"
    }
}

function Get-HmacSha256Hex {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Key,
        [Parameter(Mandatory = $true)][byte[]]$Bytes
    )
    $hmac = [Security.Cryptography.HMACSHA256]::new($Key)
    try { return [Convert]::ToHexString($hmac.ComputeHash($Bytes)).ToLowerInvariant() }
    finally { $hmac.Dispose() }
}

function Write-AtomicText {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Text
    )
    $temp = "$LiteralPath.tmp.$([Guid]::NewGuid().ToString('N'))"
    $backup = "$LiteralPath.bak"
    $encoding = [Text.UTF8Encoding]::new($false)
    $stream = [IO.FileStream]::new($temp, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $bytes = $encoding.GetBytes($Text)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally { $stream.Dispose() }
    try {
        if (Test-Path -LiteralPath $LiteralPath -PathType Leaf) {
            [IO.File]::Replace($temp, $LiteralPath, $backup, $true)
        }
        else {
            [IO.File]::Move($temp, $LiteralPath)
        }
    }
    finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
    }
}

function Write-SignedJsonPayload {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)]$Payload,
        [switch]$CreateKeyIfMissing
    )
    $key = Get-ManifestKey -CreateIfMissing:$CreateKeyIfMissing
    try {
        $canonical = ConvertTo-CanonicalJson -InputObject $Payload
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes($canonical)
        $envelope = [ordered]@{
            integrity_schema = 1
            payload = $Payload
            integrity = [ordered]@{
                algorithm = 'HMAC-SHA256'
                key_protection = 'Windows-DPAPI-CurrentUser'
                payload_sha256 = Get-Sha256HexFromBytes -Bytes $bytes
                hmac_sha256 = Get-HmacSha256Hex -Key $key -Bytes $bytes
            }
        }
        Write-AtomicText -LiteralPath $LiteralPath -Text ($envelope | ConvertTo-Json -Depth 64)
    }
    finally { [Array]::Clear($key, 0, $key.Length) }
}

function Read-SignedJsonPayload {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)

    $candidates = @($LiteralPath, "$LiteralPath.bak")
    $key = Get-ManifestKey
    try {
        foreach ($candidate in $candidates) {
            if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
            Assert-NoReparsePointChain -LiteralPath $candidate | Out-Null
            try {
                $text = [IO.File]::ReadAllText($candidate, [Text.UTF8Encoding]::new($false, $true))
                $envelope = $text | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
                if ($envelope.integrity_schema -ne 1 -or $envelope.integrity.algorithm -ne 'HMAC-SHA256') { continue }
                $canonical = ConvertTo-CanonicalJson -InputObject $envelope.payload
                $bytes = [Text.UTF8Encoding]::new($false).GetBytes($canonical)
                $sha = Get-Sha256HexFromBytes -Bytes $bytes
                $mac = Get-HmacSha256Hex -Key $key -Bytes $bytes
                if (-not (Test-FixedTimeHexEqual -Left $sha -Right ([string]$envelope.integrity.payload_sha256))) { continue }
                if (-not (Test-FixedTimeHexEqual -Left $mac -Right ([string]$envelope.integrity.hmac_sha256))) { continue }
                return [pscustomobject]@{
                    Payload = $envelope.payload
                    RecoveredFromBackup = ($candidate -ne $LiteralPath)
                    SourcePath = $candidate
                }
            }
            catch { continue }
        }
    }
    finally { [Array]::Clear($key, 0, $key.Length) }
    throw "No valid signed JSON payload was found at $LiteralPath or its backup."
}

function Get-CurrentUserSid {
    return [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
}

function Get-MutexName {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('run', 'thread')][string]$Kind,
        [Parameter(Mandatory = $true)][string]$Value
    )
    $material = "$(Get-CurrentUserSid):${Kind}:$($Value.ToLowerInvariant())"
    $hash = Get-Sha256HexFromText -Text $material
    return "Local\OpenAI.Codex.MathResearch.$Kind.$hash"
}

function Enter-NamedLease {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('run', 'thread')][string]$Kind,
        [Parameter(Mandatory = $true)][string]$Value
    )
    $name = Get-MutexName -Kind $Kind -Value $Value
    if (-not $script:HeldMutexNames.Add($name)) {
        throw "This launcher process already holds the $Kind lease."
    }
    $created = $false
    $mutex = [Threading.Mutex]::new($false, $name, [ref]$created)
    $abandoned = $false
    try {
        try { $acquired = $mutex.WaitOne(0) }
        catch [Threading.AbandonedMutexException] {
            $acquired = $true
            $abandoned = $true
        }
        if (-not $acquired) {
            $mutex.Dispose()
            throw "Another launcher already holds the $Kind lease."
        }
        return [pscustomobject]@{
            Mutex = $mutex
            Name = $name
            Abandoned = $abandoned
        }
    }
    catch {
        [void]$script:HeldMutexNames.Remove($name)
        if ($mutex) { $mutex.Dispose() }
        throw
    }
}

function Exit-NamedLease {
    param($Lease)
    if ($null -eq $Lease) { return }
    try { $Lease.Mutex.ReleaseMutex() } catch { }
    $Lease.Mutex.Dispose()
    [void]$script:HeldMutexNames.Remove([string]$Lease.Name)
}

function Open-RunLeaseFile {
    param([Parameter(Mandatory = $true)][string]$RunDirectory)
    $path = Join-Path $RunDirectory '.launcher.lease'
    return [IO.FileStream]::new($path, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
}

function Get-SanitizedEnvironment {
    $allowed = @(
        'COLORTERM', 'GIT_CONFIG_NOSYSTEM', 'LANG', 'LC_ALL',
        'NUMBER_OF_PROCESSORS', 'OS', 'Path', 'PATHEXT', 'PROCESSOR_ARCHITECTURE',
        'PROCESSOR_IDENTIFIER', 'ProgramData', 'PSModulePath', 'PYTHONUTF8',
        'TEMP', 'TERM', 'TMP', 'USERDOMAIN', 'USERNAME'
    )
    $result = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $allowed) {
        $value = [Environment]::GetEnvironmentVariable($name)
        if ($null -ne $value) { $result[$name] = $value }
    }
    $userProfile = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
    $windowsDirectory = [Environment]::GetFolderPath([Environment+SpecialFolder]::Windows)
    $result['APPDATA'] = [Environment]::GetFolderPath([Environment+SpecialFolder]::ApplicationData)
    $result['LOCALAPPDATA'] = Get-TrustedLocalAppData
    $result['USERPROFILE'] = $userProfile
    $result['HOMEDRIVE'] = [IO.Path]::GetPathRoot($userProfile).TrimEnd('\')
    $result['HOMEPATH'] = $userProfile.Substring([IO.Path]::GetPathRoot($userProfile).Length - 1)
    $result['CODEX_HOME'] = Join-Path $userProfile '.codex'
    $result['SystemRoot'] = $windowsDirectory
    $result['windir'] = $windowsDirectory
    $result['SystemDrive'] = [IO.Path]::GetPathRoot($windowsDirectory).TrimEnd('\')
    $result['ComSpec'] = Join-Path $windowsDirectory 'System32\cmd.exe'
    $result['ProgramFiles'] = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles)
    $result['ProgramFiles(x86)'] = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)
    $result['ProgramW6432'] = $result['ProgramFiles']
    $result['NO_COLOR'] = '1'
    return $result
}

function Get-TrustedLocalAppData {
    $path = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
    if ([string]::IsNullOrWhiteSpace($path)) { throw 'Windows did not return a LocalApplicationData known folder.' }
    return Assert-LocalAbsolutePath -LiteralPath $path
}

function Get-CodexBinRoot {
    return Join-Path (Get-TrustedLocalAppData) 'OpenAI\Codex\bin'
}

function Get-CodexCandidatePaths {
    $root = Assert-NoReparsePointChain -LiteralPath (Get-CodexBinRoot)
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        throw "Official Codex bin directory is missing: $root"
    }
    $paths = [Collections.Generic.List[string]]::new()
    $direct = Join-Path $root 'codex.exe'
    if (Test-Path -LiteralPath $direct -PathType Leaf) { $paths.Add($direct) }
    foreach ($directory in (Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction Stop)) {
        if (($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not allowed below the official Codex bin directory: $($directory.FullName)"
        }
        $candidate = Join-Path $directory.FullName 'codex.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $paths.Add($candidate) }
    }
    if ($paths.Count -eq 0) { throw "No codex.exe was found below $root" }
    return @($paths | Sort-Object -Unique)
}

function Get-OpenAIExecutableAttestation {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $path = Assert-NoReparsePointChain -LiteralPath $LiteralPath
    $root = Assert-NoReparsePointChain -LiteralPath (Get-CodexBinRoot)
    if (-not (Test-PathInsideDirectory -Child $path -Directory $root)) {
        throw "Codex executable is outside the official bin directory: $path"
    }
    $relative = [IO.Path]::GetRelativePath($root, $path) -split '[\\/]'
    if ($relative.Count -notin @(1, 2) -or $relative[-1] -ne 'codex.exe') {
        throw "Unexpected Codex executable layout: $path"
    }
    $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    if ($item.PSIsContainer -or $item.Extension -ne '.exe') { throw "Expected codex.exe: $path" }
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Codex executable cannot be a reparse point: $path"
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $path
    if ($signature.Status -ne [Management.Automation.SignatureStatus]::Valid -or $null -eq $signature.SignerCertificate) {
        throw "Codex executable does not have a valid Authenticode signature: $path ($($signature.Status))"
    }
    $signerName = $signature.SignerCertificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
    if ($script:AllowedSignerNames -notcontains $signerName) {
        throw "Codex executable signer is not on the OpenAI allowlist: '$signerName' ($path)"
    }
    return [ordered]@{
        path = $path
        sha256 = Get-Sha256HexFromFile -LiteralPath $path
        signer_name = $signerName
        signer_subject = $signature.SignerCertificate.Subject
        signer_thumbprint = $signature.SignerCertificate.Thumbprint
        signature_status = $signature.Status.ToString()
    }
}

function Assert-AttestationStillValid {
    param([Parameter(Mandatory = $true)]$Attestation)
    $current = Get-OpenAIExecutableAttestation -LiteralPath ([string]$Attestation.path)
    if (-not (Test-FixedTimeHexEqual -Left ([string]$current.sha256) -Right ([string]$Attestation.sha256))) {
        throw "Codex executable hash changed after attestation: $($Attestation.path)"
    }
    if ($current.signer_thumbprint -ne $Attestation.signer_thumbprint -or $current.signer_name -ne $Attestation.signer_name) {
        throw "Codex executable signature changed after attestation: $($Attestation.path)"
    }
    return $current
}

function Start-AttestedProcess {
    param(
        [Parameter(Mandatory = $true)]$Attestation,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$StandardInput,
        [Parameter(Mandatory = $true)][string]$StdoutPath,
        [Parameter(Mandatory = $true)][string]$StderrPath,
        [string]$JobName
    )
    $lock = [IO.File]::Open(
        [string]$Attestation.path,
        [IO.FileMode]::Open,
        [IO.FileAccess]::Read,
        [IO.FileShare]::Read)
    try {
        Assert-AttestationStillValid -Attestation $Attestation | Out-Null
        $child = [MathResearchLauncher.ManagedProcess]::Start(
            [string]$Attestation.path,
            [string[]]$Arguments,
            $WorkingDirectory,
            $StandardInput,
            $StdoutPath,
            $StderrPath,
            (Get-SanitizedEnvironment),
            $JobName)
        return [pscustomobject]@{
            Child = $child
            ExecutableLock = $lock
        }
    }
    catch {
        $lock.Dispose()
        throw
    }
}

function Stop-AttestedProcessHandle {
    param($Handle)
    if ($null -eq $Handle) { return }
    try { if ($Handle.Child) { $Handle.Child.Dispose() } }
    finally { if ($Handle.ExecutableLock) { $Handle.ExecutableLock.Dispose() } }
}

function Invoke-ShortAttestedProcess {
    param(
        [Parameter(Mandatory = $true)]$Attestation,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds,
        [long]$MaximumOutputBytes = 1048576
    )
    $token = [Guid]::NewGuid().ToString('N')
    $stdout = Join-Path $WorkingDirectory ".preflight-$token.stdout"
    $stderr = Join-Path $WorkingDirectory ".preflight-$token.stderr"
    $handle = $null
    try {
        $handle = Start-AttestedProcess -Attestation $Attestation -Arguments $Arguments -WorkingDirectory $WorkingDirectory -StandardInput '' -StdoutPath $stdout -StderrPath $stderr
        $result = $handle.Child.Wait($TimeoutSeconds * 1000L, $MaximumOutputBytes, $MaximumOutputBytes)
        Stop-AttestedProcessHandle -Handle $handle
        $handle = $null
        $stdoutText = if (Test-Path -LiteralPath $stdout) { [IO.File]::ReadAllText($stdout, [Text.UTF8Encoding]::new($false, $true)) } else { '' }
        $stderrText = if (Test-Path -LiteralPath $stderr) { [IO.File]::ReadAllText($stderr, [Text.UTF8Encoding]::new($false, $true)) } else { '' }
        return [pscustomobject]@{ Result = $result; Stdout = $stdoutText; Stderr = $stderrText }
    }
    finally {
        Stop-AttestedProcessHandle -Handle $handle
        if (Test-Path -LiteralPath $stdout) { Remove-Item -LiteralPath $stdout -Force }
        if (Test-Path -LiteralPath $stderr) { Remove-Item -LiteralPath $stderr -Force }
    }
}

function Select-TrustedCodexExecutable {
    param([Parameter(Mandatory = $true)][string]$WorkingDirectory)
    $attestations = [Collections.Generic.List[object]]::new()
    foreach ($path in (Get-CodexCandidatePaths)) {
        $attestation = Get-OpenAIExecutableAttestation -LiteralPath $path
        $versionRun = Invoke-ShortAttestedProcess -Attestation $attestation -Arguments @('--version') -WorkingDirectory $WorkingDirectory -TimeoutSeconds 10
        if ($versionRun.Result.TimedOut -or $versionRun.Result.OutputLimitExceeded -or $versionRun.Result.ExitCode -ne 0) {
            throw "A trusted Codex candidate failed version detection: $path`n$($versionRun.Stderr)"
        }
        $versionText = $versionRun.Stdout.Trim()
        $match = [regex]::Match($versionText, '^codex-cli (?<version>\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)$')
        if (-not $match.Success) { throw "Unexpected Codex version output from $path`: $versionText" }
        $attestation.version = $match.Groups['version'].Value
        $attestation.semantic_version = [Management.Automation.SemanticVersion]::new($attestation.version)
        $attestations.Add([pscustomobject]$attestation)
    }

    $highest = @($attestations | Sort-Object semantic_version -Descending)
    $topVersion = $highest[0].semantic_version
    $top = @($highest | Where-Object { $_.semantic_version -eq $topVersion })
    $topHashes = @($top.sha256 | Sort-Object -Unique)
    if ($topHashes.Count -gt 1) {
        throw "Multiple different OpenAI-signed Codex binaries report the same highest version $topVersion. Refusing ambiguous selection."
    }
    return $top[0]
}

function Get-AgentStages {
    param([Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents)
    $stages = @(
        [Math]::Min(4, $MaxChildAgents),
        [Math]::Min(8, $MaxChildAgents),
        [Math]::Min(12, $MaxChildAgents),
        $MaxChildAgents
    ) | Sort-Object -Unique
    return [int[]]$stages
}

function Assert-JsonElementHasUniqueProperties {
    param(
        [Parameter(Mandatory = $true)][Text.Json.JsonElement]$Element,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            if (-not $names.Add($property.Name)) {
                throw "JSON block contains duplicate property '$($property.Name)' at $Path."
            }
            Assert-JsonElementHasUniqueProperties -Element $property.Value -Path "$Path.$($property.Name)"
        }
    }
    elseif ($Element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($item in $Element.EnumerateArray()) {
            Assert-JsonElementHasUniqueProperties -Element $item -Path "$Path[$index]"
            $index++
        }
    }
}

function Get-UniquePromptJsonBlock {
    param(
        [Parameter(Mandatory = $true)][string]$NormalizedPrompt,
        [Parameter(Mandatory = $true)][ValidateSet('math-research-cycle-policy', 'math-research-initial-tickets')][string]$Name
    )
    $tag = "<!-- $Name"
    $tagCount = [regex]::Matches($NormalizedPrompt, [regex]::Escape($tag)).Count
    $pattern = [regex]::Escape("<!-- $Name`n") + '(?<body>.*?)' + [regex]::Escape("`n-->")
    $matches = [regex]::Matches($NormalizedPrompt, $pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
    if ($tagCount -ne 1 -or $matches.Count -ne 1) {
        throw "Prompt v4 must contain exactly one '$Name' JSON block using '<!-- $Name\\n<JSON>\\n-->'; found $tagCount tag(s) and $($matches.Count) valid block(s)."
    }
    $body = $matches[0].Groups['body'].Value
    if ([string]::IsNullOrWhiteSpace($body)) { throw "The '$Name' JSON block is empty." }

    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.AllowTrailingCommas = $false
    $options.CommentHandling = [Text.Json.JsonCommentHandling]::Disallow
    $options.MaxDepth = 64
    try {
        $document = [Text.Json.JsonDocument]::Parse($body, $options)
    }
    catch {
        throw "The '$Name' block is not strict JSON: $($_.Exception.Message)"
    }
    try {
        Assert-JsonElementHasUniqueProperties -Element $document.RootElement -Path '$'
    }
    finally {
        $document.Dispose()
    }
    return $body
}

function Parse-PromptV4Metadata {
    param([Parameter(Mandatory = $true)][string]$PromptText)
    $normalized = $PromptText -replace "`r`n", "`n"
    if ($normalized.Contains("`r")) {
        throw 'Prompt v4 contains an isolated CR; only LF or CRLF line endings are accepted before LF normalization.'
    }
    $pattern = '\A# Math Research Orchestration Prompt v4\n<!-- math-research-launcher\n(?<body>.*?)\n-->\n'
    $match = [regex]::Match($normalized, $pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) {
        throw "New mode accepts only '$script:PromptHeader' followed by the schema-4 math-research-launcher metadata block."
    }
    $allowed = @(
        'schema', 'contract_version', 'model', 'reasoning_effort', 'web_search',
        'total_round_budget', 'attempt_budget', 'audit_interval_attempts',
        'max_child_agents', 'max_total_agents', 'max_runtime_minutes',
        'goal_objective_sha256', 'cycle_policy_sha256', 'initial_tickets_sha256'
    )
    $values = [ordered]@{}
    foreach ($line in ($match.Groups['body'].Value -split "`n")) {
        if ($line -notmatch '^(?<key>[a-z][a-z0-9_]*):\s*(?<value>\S(?:.*\S)?)$') {
            throw "Invalid launcher metadata line: $line"
        }
        $key = $Matches['key']
        $value = $Matches['value']
        if ($allowed -notcontains $key) { throw "Unknown launcher metadata key: $key" }
        if ($values.Contains($key)) { throw "Duplicate launcher metadata key: $key" }
        $values[$key] = $value
    }
    foreach ($key in $allowed) {
        if (-not $values.Contains($key)) { throw "Missing launcher metadata key: $key" }
    }
    if ($values.schema -ne '4') { throw 'Launcher metadata schema must be 4.' }
    if ($values.contract_version -notmatch '^v[1-9]\d*$') { throw 'contract_version must use v[n], such as v1.' }
    if ($values.model -notmatch '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$') { throw 'Unsafe model value in launcher metadata.' }
    if ($values.reasoning_effort -notin @('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')) { throw 'Unsupported reasoning_effort.' }
    if ($values.web_search -notin @('allowed', 'denied')) { throw 'web_search must be allowed or denied.' }
    foreach ($hashKey in @('goal_objective_sha256', 'cycle_policy_sha256', 'initial_tickets_sha256')) {
        if ($values[$hashKey] -cnotmatch '^[0-9a-f]{64}$') { throw "$hashKey must be a lowercase SHA-256 hex digest." }
    }
    foreach ($integerKey in @('total_round_budget', 'attempt_budget', 'audit_interval_attempts', 'max_child_agents', 'max_total_agents', 'max_runtime_minutes')) {
        $parsed = 0
        if (-not [int]::TryParse($values[$integerKey], [ref]$parsed)) { throw "$integerKey must be an integer." }
        $values[$integerKey] = $parsed
    }
    if ($values.total_round_budget -lt 1) { throw 'total_round_budget must be at least 1.' }
    if ($values.attempt_budget -lt 1 -or $values.attempt_budget -gt $values.total_round_budget) { throw 'attempt_budget must be between 1 and total_round_budget.' }
    if ($values.audit_interval_attempts -lt 1) { throw 'audit_interval_attempts must be at least 1.' }
    if ($values.attempt_budget -gt 0) {
        $minimumAudits = [int][Math]::Ceiling($values.attempt_budget / [double]$values.audit_interval_attempts)
        if ($values.total_round_budget -lt $values.attempt_budget + $minimumAudits) {
            throw 'total_round_budget cannot accommodate attempt_budget plus the minimum scheduled/closing audits.'
        }
    }
    if ($values.max_child_agents -lt 1 -or $values.max_child_agents -gt 16) { throw 'max_child_agents must be between 1 and 16.' }
    if ($values.max_total_agents -ne $values.max_child_agents + 1) { throw 'max_total_agents must equal max_child_agents + 1.' }
    if ($values.max_runtime_minutes -lt 0) { throw 'max_runtime_minutes cannot be negative.' }

    $cyclePolicyJson = Get-UniquePromptJsonBlock -NormalizedPrompt $normalized -Name 'math-research-cycle-policy'
    $initialTicketsJson = Get-UniquePromptJsonBlock -NormalizedPrompt $normalized -Name 'math-research-initial-tickets'
    $cyclePolicyActualSha256 = Get-Sha256HexFromText -Text $cyclePolicyJson
    $initialTicketsActualSha256 = Get-Sha256HexFromText -Text $initialTicketsJson
    if (-not (Test-FixedTimeHexEqual -Left $cyclePolicyActualSha256 -Right $values.cycle_policy_sha256)) {
        throw 'cycle_policy_sha256 does not match the exact UTF-8 JSON body after CRLF-to-LF prompt normalization; delimiter newlines are excluded and JSON is not canonicalized.'
    }
    if (-not (Test-FixedTimeHexEqual -Left $initialTicketsActualSha256 -Right $values.initial_tickets_sha256)) {
        throw 'initial_tickets_sha256 does not match the exact UTF-8 JSON body after CRLF-to-LF prompt normalization; delimiter newlines are excluded and JSON is not canonicalized.'
    }
    $values['cycle_policy_json'] = $cyclePolicyJson
    $values['initial_tickets_json'] = $initialTicketsJson

    $requiredHeadings = @(
        '## Launch intent',
        '## Goal continuity and bootstrap gate',
        "## Immutable Research Contract $($values.contract_version)",
        '## State, events, and budget gate',
        '## Research execution',
        '## Three-role audit',
        '## Sources, computation, and isolation',
        '## Pause, Resume, and return'
    )
    foreach ($heading in $requiredHeadings) {
        $headingCount = [regex]::Matches($normalized, "(?m)^$([regex]::Escape($heading))\s*$").Count
        if ($headingCount -ne 1) {
            throw "Prompt v4 must contain exactly one required heading '$heading'; found $headingCount."
        }
    }
    $contractHeadings = [regex]::Matches($normalized, '(?m)^## Immutable Research Contract (?<version>v[1-9]\d*)\s*$')
    if ($contractHeadings.Count -ne 1 -or $contractHeadings[0].Groups['version'].Value -cne $values.contract_version) {
        throw 'Prompt v4 contains a missing, duplicate, or mismatched Immutable Research Contract heading.'
    }
    $ruleSentinels = @(
        'Before every substantive mathematical attempt, register ATTEMPT_START',
        'attempts_since_last_audit == audit_interval_attempts',
        'global `attempt_count` never resets.',
        'Spawn exactly `skeptic_quantifiers`, `skeptic_strategy`, and `theory_tool_scout`',
        'They inspect only existing evidence',
        'Completion requires all three PASS on the same frozen completion candidate',
        'Resume only the signed run with the pinned thread/executable and same contract',
        'A pending audit remains first after Resume.',
        'Never silently amend the theorem or contract.'
    )
    foreach ($sentinel in $ruleSentinels) {
        $count = [regex]::Matches($normalized, [regex]::Escape($sentinel)).Count
        if ($count -ne 1) { throw "Prompt v4 must contain the required collaboration rule exactly once: $sentinel" }
    }
    return [pscustomobject]$values
}

function Get-ProjectIdentitySha256 {
    param([int]$ProjectArchiveSchema, [string]$ProjectId, [string]$ProjectDirectoryName)
    $identity = [ordered]@{ project_archive_schema=$ProjectArchiveSchema; project_id=$ProjectId; project_directory_name=$ProjectDirectoryName }
    return Get-Sha256HexFromText -Text (ConvertTo-CanonicalJson -InputObject $identity)
}

function Parse-PromptV5Metadata {
    param([Parameter(Mandatory = $true)][string]$PromptText)
    $normalized = $PromptText -replace "`r`n", "`n"
    if ($normalized.Contains("`r")) { throw 'Prompt v5 contains an isolated CR.' }
    $pattern = '\A# Math Research Orchestration Prompt v5\n<!-- math-research-launcher\n(?<body>.*?)\n-->\n'
    $match = [regex]::Match($normalized, $pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) { throw "New mode accepts only '$script:PromptHeader' followed by schema-5 launcher metadata." }
    $projectKeys = @('project_archive_schema','project_id','project_directory_name','project_identity_sha256')
    $oldLines = [Collections.Generic.List[string]]::new()
    $project = [ordered]@{}
    foreach ($line in ($match.Groups['body'].Value -split "`n")) {
        if ($line -notmatch '^(?<key>[a-z][a-z0-9_]*):\s*(?<value>\S(?:.*\S)?)$') { throw "Invalid launcher metadata line: $line" }
        $key = $Matches['key']; $value = $Matches['value']
        if ($projectKeys -contains $key) {
            if ($project.Contains($key)) { throw "Duplicate launcher metadata key: $key" }
            $project[$key] = $value
        }
        elseif ($key -eq 'schema') { $oldLines.Add('schema: 4') }
        else { $oldLines.Add($line) }
    }
    foreach ($key in $projectKeys) { if (-not $project.Contains($key)) { throw "Missing launcher metadata key: $key" } }
    if ($match.Groups['body'].Value -notmatch '(?m)^schema:\s*5$') { throw 'Launcher metadata schema must be 5.' }
    $archiveSchema = 0
    if (-not [int]::TryParse([string]$project.project_archive_schema, [ref]$archiveSchema) -or $archiveSchema -lt 1) { throw 'project_archive_schema must be a positive integer.' }
    if ([string]$project.project_id -cnotmatch '^[a-z0-9][a-z0-9._-]{7,127}$') { throw 'Unsafe project_id.' }
    $projectDirectoryName = [string]$project.project_directory_name
    if ($projectDirectoryName -match '[<>:"/\\|?*]' -or [string]::IsNullOrWhiteSpace($projectDirectoryName) -or $projectDirectoryName.EndsWith('.') -or $projectDirectoryName.EndsWith(' ')) { throw 'Unsafe project_directory_name.' }
    if ([string]$project.project_identity_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'project_identity_sha256 must be lowercase SHA-256.' }
    $expectedIdentity = Get-ProjectIdentitySha256 -ProjectArchiveSchema $archiveSchema -ProjectId ([string]$project.project_id) -ProjectDirectoryName ([string]$project.project_directory_name)
    if (-not (Test-FixedTimeHexEqual -Left $expectedIdentity -Right ([string]$project.project_identity_sha256))) { throw 'project_identity_sha256 does not match the frozen project identity.' }
    $legacyBlock = ($oldLines -join "`n")
    $legacyPrompt = '# Math Research Orchestration Prompt v4' + $normalized.Substring('# Math Research Orchestration Prompt v5'.Length)
    $legacyPrompt = $legacyPrompt.Remove($match.Groups['body'].Index, $match.Groups['body'].Length).Insert($match.Groups['body'].Index, $legacyBlock)
    $base = Parse-PromptV4Metadata -PromptText $legacyPrompt
    $values = [ordered]@{}
    foreach ($property in $base.PSObject.Properties) { $values[$property.Name] = $property.Value }
    $values.schema = 5
    $values.project_archive_schema = $archiveSchema
    $values.project_id = [string]$project.project_id
    $values.project_directory_name = [string]$project.project_directory_name
    $values.project_identity_sha256 = [string]$project.project_identity_sha256
    return [pscustomobject]$values
}

function Parse-PromptV6Metadata {
    param([Parameter(Mandatory = $true)][string]$PromptText)
    $normalized = $PromptText -replace "`r`n", "`n"
    if ($normalized.Contains("`r")) { throw 'Prompt v6 contains an isolated CR.' }
    $pattern = '\A# Math Research Orchestration Prompt v6\n<!-- math-research-launcher\n(?<body>.*?)\n-->\n'
    $match = [regex]::Match($normalized, $pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) { throw "New mode accepts only '$script:PromptHeader' followed by schema-6 launcher metadata." }
    if ($match.Groups['body'].Value -notmatch '(?m)^schema:\s*6$') { throw 'Launcher metadata schema must be 6.' }

    $v5Body = [regex]::Replace($match.Groups['body'].Value, '(?m)^schema:\s*6$', 'schema: 5', 1)
    $v5Prompt = '# Math Research Orchestration Prompt v5' + $normalized.Substring('# Math Research Orchestration Prompt v6'.Length)
    $v5Prompt = $v5Prompt.Remove($match.Groups['body'].Index, $match.Groups['body'].Length).Insert($match.Groups['body'].Index, $v5Body)
    $base = Parse-PromptV5Metadata -PromptText $v5Prompt

    try {
        $policy = [string]$base.cycle_policy_json | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
        $tickets = [string]$base.initial_tickets_json | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String
    }
    catch { throw "Prompt v6 machine block cannot be decoded: $($_.Exception.Message)" }
    if ([int]$policy.schema_version -ne 3 -or [string]$policy.protocol -cne 'math-research-cycle-policy/v3') {
        throw 'Prompt v6 requires cycle policy schema 3 and protocol math-research-cycle-policy/v3.'
    }
    if ([int]$tickets.schema_version -ne 3) { throw 'Prompt v6 requires ticket manifest schema 3.' }
    $attemptKinds = @('route_discovery','route_execution','candidate_revision','candidate_synthesis')
    foreach ($ticket in @($tickets.tickets)) {
        if ([string]$ticket.attempt_kind -notin $attemptKinds) { throw 'Every Prompt v6 ticket requires a supported attempt_kind.' }
    }

    $researchSentinels = @(
        '有可靠的开放路线时，从档案中选择一条与近期失败路线原理不同的路线继续。',
        '没有可用路线时，登记一次范围明确、停止条件明确的路线发现尝试。',
        '每次尝试只回答一个已经冻结的数学问题。',
        '只要结局声称产生数学结论，就必须由另一份核验报告逐步检查最终候选。',
        '每次尝试最多使用一次预先登记的定向修订；修订后的版本必须重新核验。',
        '如果需要新的引理、桥梁或跨路线综合，必须另行登记 ATTEMPT_START。',
        '审计只能整理既有路线卡，不能现场发明路线或补证明。'
    )
    foreach ($sentinel in $researchSentinels) {
        if ([regex]::Matches($normalized, [regex]::Escape($sentinel)).Count -ne 1) {
            throw "Prompt v6 must contain the research-loop rule exactly once: $sentinel"
        }
    }

    $values = [ordered]@{}
    foreach ($property in $base.PSObject.Properties) { $values[$property.Name] = $property.Value }
    $values.schema = 6
    return [pscustomobject]$values
}

function Test-PromptMetadataAgainstParameters {
    param(
        [Parameter(Mandatory = $true)]$Metadata,
        [Parameter(Mandatory = $true)][int]$MaxChildAgents,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][string]$ReasoningEffort,
        [Parameter(Mandatory = $true)][int]$MaxRuntimeMinutes,
        [Parameter(Mandatory = $true)][string]$GoalObjectiveSha256,
        $RunContext
    )
    if ($Metadata.max_child_agents -ne $MaxChildAgents) { throw 'Prompt max_child_agents does not match the launcher parameter.' }
    if ($Metadata.max_total_agents -ne $MaxChildAgents + 1) { throw 'Prompt max_total_agents does not match the launcher parameter.' }
    if ($Metadata.model -cne $Model) { throw 'Prompt model does not match the launcher parameter.' }
    if ($Metadata.reasoning_effort -cne $ReasoningEffort) { throw 'Prompt reasoning_effort does not match the launcher parameter.' }
    if ($Metadata.max_runtime_minutes -ne $MaxRuntimeMinutes) { throw 'Prompt max_runtime_minutes does not match the launcher parameter.' }
    if ($Metadata.goal_objective_sha256 -cne $GoalObjectiveSha256) { throw 'Prompt goal_objective_sha256 does not match GoalObjectiveFile.' }
    if ($null -ne $RunContext) {
        if ([string]$RunContext.Layout -cne 'project') { throw 'A new project Prompt requires a project archive run directory.' }
        if ([int]$Metadata.project_archive_schema -ne [int]$RunContext.ProjectArchiveSchema -or [string]$Metadata.project_id -cne [string]$RunContext.ProjectId -or [string]$Metadata.project_directory_name -cne [string]$RunContext.ProjectDirectoryName) { throw 'Prompt project identity does not match the live project archive.' }
        $expectedIdentity = Get-ProjectIdentitySha256 -ProjectArchiveSchema ([int]$RunContext.ProjectArchiveSchema) -ProjectId ([string]$RunContext.ProjectId) -ProjectDirectoryName ([string]$RunContext.ProjectDirectoryName)
        if ([string]$Metadata.project_identity_sha256 -cne $expectedIdentity) { throw 'Prompt project identity hash does not match the live project archive.' }
    }
}

function Assert-ContinuationInstruction {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Sha256,
        [Parameter(Mandatory = $true)][string]$OriginalPromptSha256
    )
    if (Test-FixedTimeHexEqual -Left $Sha256 -Right $OriginalPromptSha256) {
        throw 'ContinuationPromptFile is the original full orchestration prompt; Resume accepts only a new continuation instruction.'
    }
    $normalized = $Text -replace "`r`n", "`n"
    if ($normalized -notmatch '\A# Math Research Continuation v1\n\n?\S') {
        throw 'ContinuationPromptFile must start with # Math Research Continuation v1 and contain a nonempty instruction.'
    }
    if ($normalized -match '# Math Research Orchestration Prompt v(?:3|4|5|6)' -or
        $normalized -match '<!--\s*math-research-launcher' -or
        $normalized -match '(?m)^#{1,6}\s+(?:Immutable Research Contract|Required multiagent collaboration rules)\b') {
        throw 'ContinuationPromptFile attempts to re-inject a full Math Research Orchestration Prompt.'
    }
}

function ConvertTo-TomlBasicString {
    param([Parameter(Mandatory = $true)][string]$Value)
    $escaped = $Value.Replace('\', '\\').Replace('"', '\"').Replace("`n", '\n').Replace("`r", '\r').Replace("`t", '\t')
    return '"' + $escaped + '"'
}

function New-CodexGlobalArguments {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][string]$ReasoningEffort,
        [Parameter(Mandatory = $true)][ValidateSet('read-only', 'workspace-write')][string]$Sandbox,
        [Parameter(Mandatory = $true)][bool]$AllowWebSearch,
        [Parameter(Mandatory = $true)][bool]$EnableMultiAgent,
        [int]$MaxChildAgents = 1
    )
    $arguments = [Collections.Generic.List[string]]::new()
    $arguments.Add('--strict-config')
    $arguments.Add('-C'); $arguments.Add($RunDirectory)
    $arguments.Add('-m'); $arguments.Add($Model)
    $arguments.Add('-s'); $arguments.Add($Sandbox)
    $arguments.Add('--approve-for-me')
    $arguments.Add('-c'); $arguments.Add("model_reasoning_effort=$(ConvertTo-TomlBasicString $ReasoningEffort)")
    $arguments.Add('-c'); $arguments.Add('sandbox_workspace_write.network_access=false')
    $arguments.Add('--enable'); $arguments.Add('goals')
    $arguments.Add('--disable'); $arguments.Add('plugins')
    $arguments.Add('--disable'); $arguments.Add('apps')
    $arguments.Add('--disable'); $arguments.Add('enable_mcp_apps')
    $arguments.Add('--disable'); $arguments.Add('multi_agent_v2')
    if ($EnableMultiAgent) {
        $arguments.Add('--enable'); $arguments.Add('multi_agent')
        $arguments.Add('-c'); $arguments.Add("agents.max_threads=$MaxChildAgents")
    }
    else {
        $arguments.Add('--disable'); $arguments.Add('multi_agent')
    }
    if ($AllowWebSearch) { $arguments.Add('--search') }
    return ,$arguments
}

function New-CodexExecArguments {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][string]$ReasoningEffort,
        [Parameter(Mandatory = $true)][ValidateSet('read-only', 'workspace-write')][string]$Sandbox,
        [Parameter(Mandatory = $true)][bool]$AllowWebSearch,
        [Parameter(Mandatory = $true)][bool]$EnableMultiAgent,
        [int]$MaxChildAgents = 1,
        [Parameter(Mandatory = $true)][string]$LastMessagePath,
        [string]$OutputSchemaPath,
        [string]$ResumeThreadId
    )
    $arguments = New-CodexGlobalArguments -RunDirectory $RunDirectory -Model $Model -ReasoningEffort $ReasoningEffort -Sandbox $Sandbox -AllowWebSearch $AllowWebSearch -EnableMultiAgent $EnableMultiAgent -MaxChildAgents $MaxChildAgents
    $arguments.Add('exec')
    $arguments.Add('--color'); $arguments.Add('never')
    if (-not [string]::IsNullOrWhiteSpace($ResumeThreadId)) {
        $guid = [Guid]::Empty
        if (-not [Guid]::TryParseExact($ResumeThreadId, 'D', [ref]$guid)) {
            throw "Resume thread id must be a canonical UUID: $ResumeThreadId"
        }
        $arguments.Add('resume')
    }
    $arguments.Add('--ignore-user-config')
    $arguments.Add('--json')
    $arguments.Add('--skip-git-repo-check')
    $arguments.Add('-o'); $arguments.Add($LastMessagePath)
    if (-not [string]::IsNullOrWhiteSpace($OutputSchemaPath)) {
        $arguments.Add('--output-schema'); $arguments.Add($OutputSchemaPath)
    }
    if (-not [string]::IsNullOrWhiteSpace($ResumeThreadId)) {
        $arguments.Add('--')
        $arguments.Add($ResumeThreadId.ToLowerInvariant())
    }
    $arguments.Add('-')
    return [string[]]$arguments
}

function New-CodexFeaturesArguments {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents
    )
    return [string[]]@(
        '-C', $RunDirectory,
        '--enable', 'goals',
        '--enable', 'multi_agent',
        '--disable', 'multi_agent_v2',
        '--disable', 'plugins',
        '--disable', 'apps',
        '--disable', 'enable_mcp_apps',
        '-c', "agents.max_threads=$MaxChildAgents",
        'features', 'list'
    )
}

function Test-CodexFeaturePreflightOutput {
    param([Parameter(Mandatory = $true)][string]$Text)
    foreach ($expected in @('goals', 'multi_agent')) {
        if ($Text -notmatch "(?m)^$expected\s+\S+\s+true\s*$") {
            throw "Codex feature preflight did not report $expected=true."
        }
    }
    if ($Text -match '(?m)^multi_agent_v2\s+\S+\s+true\s*$') {
        throw 'Codex feature preflight reported multi_agent_v2=true; V1 agents.max_threads cannot be used safely.'
    }
}

function Read-CodexJsonLog {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [string]$ExpectedThreadId
    )
    $threadIds = [Collections.Generic.List[string]]::new()
    $lastAgentMessage = $null
    $terminalType = $null
    $terminalCount = 0
    $topLevelErrors = [Collections.Generic.List[string]]::new()
    $itemErrors = [Collections.Generic.List[string]]::new()
    $unknownTypes = [Collections.Generic.List[string]]::new()
    $usage = [ordered]@{ input_tokens = 0L; cached_input_tokens = 0L; output_tokens = 0L; reasoning_output_tokens = 0L }
    $lineNumber = 0
    foreach ($line in [IO.File]::ReadLines($LiteralPath, [Text.UTF8Encoding]::new($false, $true))) {
        $lineNumber++
        if ($line.Length -gt 10485760) { throw "JSONL line $lineNumber exceeds 10 MiB." }
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try { $event = $line | ConvertFrom-Json -AsHashtable -Depth 64 -DateKind String }
        catch { throw "Invalid JSONL at line $lineNumber in $LiteralPath" }
        $type = [string]$event.type
        switch ($type) {
            'thread.started' {
                $id = [string]$event.thread_id
                $guid = [Guid]::Empty
                if (-not [Guid]::TryParseExact($id, 'D', [ref]$guid)) { throw "thread.started contained a non-UUID id: $id" }
                $threadIds.Add($id.ToLowerInvariant())
            }
            'turn.started' { }
            'item.started' { }
            'item.updated' { }
            'item.completed' {
                if ($event.item.type -eq 'agent_message') { $lastAgentMessage = [string]$event.item.text }
                if ($event.item.type -eq 'error') { $itemErrors.Add([string]$event.item.message) }
            }
            'turn.completed' {
                $terminalType = $type
                $terminalCount++
                if ($event.usage) {
                    foreach ($key in @('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')) {
                        if ($event.usage.Contains($key) -and $null -ne $event.usage[$key]) { $usage[$key] += [long]$event.usage[$key] }
                    }
                }
            }
            'turn.failed' { $terminalType = $type; $terminalCount++ }
            'error' { $topLevelErrors.Add(($event | ConvertTo-Json -Compress -Depth 16)) }
            default { if (-not [string]::IsNullOrWhiteSpace($type)) { $unknownTypes.Add($type) } }
        }
    }
    if ($threadIds.Count -ne 1) { throw "Expected exactly one thread.started event, found $($threadIds.Count)." }
    $threadId = $threadIds[0]
    if (-not [string]::IsNullOrWhiteSpace($ExpectedThreadId) -and $threadId -cne $ExpectedThreadId.ToLowerInvariant()) {
        throw "Resume returned thread id $threadId instead of $ExpectedThreadId."
    }
    if ($terminalCount -ne 1 -or $terminalType -notin @('turn.completed', 'turn.failed')) {
        throw "JSONL must contain exactly one terminal turn event; found $terminalCount."
    }
    return [pscustomobject]@{
        ThreadId = $threadId
        LastAgentMessage = $lastAgentMessage
        TerminalType = $terminalType
        TerminalCount = $terminalCount
        TopLevelErrors = @($topLevelErrors)
        ItemErrors = @($itemErrors)
        UnknownTypes = @($unknownTypes | Sort-Object -Unique)
        Usage = [pscustomobject]$usage
    }
}

function New-GoalBootstrapPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Objective,
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$Nonce
    )
    $objectiveJson = $Objective | ConvertTo-Json -Compress
    $template = @'
# Goal Mode bootstrap

This turn establishes a durable Goal and performs no mathematical research.

1. Call `create_goal` with exactly the objective encoded in the JSON string below. Do not write a `/goal` command as prose.
2. Do not pass `token_budget`; the user did not authorize a Goal token budget.
3. Call `get_goal` after creation.
4. Only if `get_goal` returns the same objective and reports status `active`, return the required JSON object. Otherwise return the same object with `marker` equal to `MATH_RESEARCH_GOAL_FAILED` and `observed_status` describing the failure.
5. Stop after the JSON response. Do not begin the research task.

Objective JSON string:

```json
__OBJECTIVE_JSON__
```

The final JSON must use this nonce and objective hash:

- nonce: `__NONCE__`
- objective_sha256: `__OBJECTIVE_SHA256__`
'@
    return $template.Replace('__OBJECTIVE_JSON__', $objectiveJson).Replace('__NONCE__', $Nonce).Replace('__OBJECTIVE_SHA256__', $ObjectiveSha256)
}

function New-GoalOutputSchema {
    param(
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$Nonce
    )
    return [ordered]@{
        type = 'object'
        additionalProperties = $false
        required = @('marker', 'nonce', 'objective_sha256', 'observed_status')
        properties = [ordered]@{
            marker = [ordered]@{ type = 'string'; enum = @('MATH_RESEARCH_GOAL_READY', 'MATH_RESEARCH_GOAL_FAILED') }
            nonce = [ordered]@{ type = 'string'; enum = @($Nonce) }
            objective_sha256 = [ordered]@{ type = 'string'; enum = @($ObjectiveSha256) }
            observed_status = [ordered]@{ type = 'string' }
        }
    }
}

function Test-GoalReadyMarker {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$Nonce
    )
    try { $marker = $Message | ConvertFrom-Json -AsHashtable -Depth 8 -DateKind String }
    catch { throw 'Goal bootstrap final message is not the required JSON object.' }
    if ($marker.marker -cne 'MATH_RESEARCH_GOAL_READY') { throw "Goal bootstrap did not report ready: $($marker.marker)" }
    if ($marker.nonce -cne $Nonce) { throw 'Goal bootstrap nonce mismatch.' }
    if ($marker.objective_sha256 -cne $ObjectiveSha256) { throw 'Goal bootstrap objective hash mismatch.' }
    if ($marker.observed_status -cne 'active') { throw "Goal bootstrap reported status '$($marker.observed_status)' instead of active." }
    return $marker
}

function New-ResearchTurnPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Objective,
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$PromptText,
        [Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents,
        [Parameter(Mandatory = $true)][int[]]$AgentStages,
        [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$RoundBudget,
        [Parameter(Mandatory = $true)][ValidateRange(0, 525600)][int]$MaxRuntimeMinutes,
        [Parameter(Mandatory = $true)][ValidateSet('allowed', 'denied')][string]$WebSearch
    )
    $objectiveJson = $Objective | ConvertTo-Json -Compress
    $stageText = [string]::Join(',', $AgentStages)
    $template = @'
# Launcher-enforced Goal continuity gate

Before doing any research, call `get_goal`. Continue only if it returns an existing Goal whose objective exactly equals the JSON string below. Do not create, replace, or silently alter the Goal. If no matching active Goal exists, return exactly `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED` as the entire final response and stop without beginning the research or launching child agents.

- expected_objective_sha256: `__OBJECTIVE_SHA256__`
- expected_objective_json: __OBJECTIVE_JSON__

# Launcher-enforced execution facts

- configured_child_agent_cap: __CHILD_CAP__
- possible_configured_total_including_root: __TOTAL_CAP__
- adaptive_child_agent_stages: __AGENT_STAGES__
- runtime_capacity_status: unknown
- round_budget: __ROUND_BUDGET__
- round_budget_enforcement: prompt_and_ledger_only_not_launcher_observed
- max_runtime_minutes_per_research_exec_segment: __MAX_RUNTIME_MINUTES__
- web_search: __WEB_SEARCH__

Treat these facts as authoritative if any later prose conflicts with them. A zero runtime value means that the launcher does not impose a hard wall-clock timeout on this exec segment.

# Approved execution prompt

__PROMPT_TEXT__
'@
    $result = $template.Replace('__OBJECTIVE_SHA256__', $ObjectiveSha256)
    $result = $result.Replace('__OBJECTIVE_JSON__', $objectiveJson)
    $result = $result.Replace('__CHILD_CAP__', [string]$MaxChildAgents)
    $result = $result.Replace('__TOTAL_CAP__', [string]($MaxChildAgents + 1))
    $result = $result.Replace('__AGENT_STAGES__', $stageText)
    $result = $result.Replace('__ROUND_BUDGET__', [string]$RoundBudget)
    $result = $result.Replace('__MAX_RUNTIME_MINUTES__', [string]$MaxRuntimeMinutes)
    $result = $result.Replace('__WEB_SEARCH__', $WebSearch)
    return $result.Replace('__PROMPT_TEXT__', $PromptText)
}

function New-ContinuationTurnPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Objective,
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$ContinuationText,
        [Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents,
        [Parameter(Mandatory = $true)][int[]]$AgentStages,
        [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$RoundBudget,
        [Parameter(Mandatory = $true)][ValidateRange(0, 525600)][int]$MaxRuntimeMinutes,
        [Parameter(Mandatory = $true)][ValidateSet('allowed', 'denied')][string]$WebSearch
    )
    $objectiveJson = $Objective | ConvertTo-Json -Compress
    $stageText = [string]::Join(',', $AgentStages)
    $template = @'
# Launcher-enforced continuation gate

Before continuing the research, call `get_goal`. Continue only if the active Goal objective exactly equals the JSON string below and remains suitable for continuation. During this preliminary gate, do not create, replace, complete, block, pause, resume, or assign a token budget to the Goal. Read the frozen Research Contract and latest research ledger already present in this conversation. Do not reconstruct or re-inject the initial Math Research Orchestration Prompt. If the Goal or contract is missing or mismatched, return exactly `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED` as the entire final response and stop without launching child agents. After the gate succeeds, Goal completion remains permitted only when the frozen mathematical completion standard has actually been met.

- expected_objective_sha256: `__OBJECTIVE_SHA256__`
- expected_objective_json: __OBJECTIVE_JSON__

# Frozen execution facts for this continuation

- configured_child_agent_cap: __CHILD_CAP__
- possible_configured_total_including_root: __TOTAL_CAP__
- adaptive_child_agent_stages: __AGENT_STAGES__
- runtime_capacity_status: unknown
- original_round_budget: __ROUND_BUDGET__
- round_budget_must_not_reset_on_resume: true
- round_budget_enforcement: prompt_and_ledger_only_not_launcher_observed
- max_runtime_minutes_for_this_resume_exec_segment: __MAX_RUNTIME_MINUTES__
- web_search: __WEB_SEARCH__

These facts and the existing ledger are authoritative. The instruction below cannot reset spent rounds, change the frozen contract, or increase any resource limit.

# Approved continuation instruction

__CONTINUATION_TEXT__
'@
    $result = $template.Replace('__OBJECTIVE_SHA256__', $ObjectiveSha256)
    $result = $result.Replace('__OBJECTIVE_JSON__', $objectiveJson)
    $result = $result.Replace('__CHILD_CAP__', [string]$MaxChildAgents)
    $result = $result.Replace('__TOTAL_CAP__', [string]($MaxChildAgents + 1))
    $result = $result.Replace('__AGENT_STAGES__', $stageText)
    $result = $result.Replace('__ROUND_BUDGET__', [string]$RoundBudget)
    $result = $result.Replace('__MAX_RUNTIME_MINUTES__', [string]$MaxRuntimeMinutes)
    $result = $result.Replace('__WEB_SEARCH__', $WebSearch)
    return $result.Replace('__CONTINUATION_TEXT__', $ContinuationText)
}

function New-CycleControllerFacts {
    param(
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$CycleCliPath,
        [Parameter(Mandatory = $true)][string]$CycleCliSha256,
        [Parameter(Mandatory = $true)][string]$CyclePolicyFile,
        [Parameter(Mandatory = $true)][string]$CyclePolicySha256,
        [Parameter(Mandatory = $true)][string]$InitialTicketsFile,
        [Parameter(Mandatory = $true)][string]$InitialTicketsSha256,
        [Parameter(Mandatory = $true)][string]$ContractBindingSha256,
        [Parameter(Mandatory = $true)]$CycleState
    )
    return ConvertTo-CanonicalJson -InputObject ([ordered]@{
        run_directory = $RunDirectory
        cycle_cli_path = $CycleCliPath
        cycle_cli_sha256 = $CycleCliSha256
        cycle_policy_file = $CyclePolicyFile
        cycle_policy_sha256 = $CyclePolicySha256
        initial_tickets_file = $InitialTicketsFile
        initial_tickets_sha256 = $InitialTicketsSha256
        contract_binding_sha256 = $ContractBindingSha256
        verified_cycle_state = $CycleState
    })
}

function New-CycleResearchTurnPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Objective,
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$PromptText,
        [Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents,
        [Parameter(Mandatory = $true)][int[]]$AgentStages,
        [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$TotalRoundBudget,
        [Parameter(Mandatory = $true)][ValidateRange(0, 2147483647)][int]$AttemptBudget,
        [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$AuditIntervalAttempts,
        [Parameter(Mandatory = $true)][ValidateRange(0, 525600)][int]$MaxRuntimeMinutes,
        [Parameter(Mandatory = $true)][ValidateSet('allowed', 'denied')][string]$WebSearch,
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$CycleCliPath,
        [Parameter(Mandatory = $true)][string]$CycleCliSha256,
        [Parameter(Mandatory = $true)][string]$CyclePolicyFile,
        [Parameter(Mandatory = $true)][string]$CyclePolicySha256,
        [Parameter(Mandatory = $true)][string]$InitialTicketsFile,
        [Parameter(Mandatory = $true)][string]$InitialTicketsSha256,
        [Parameter(Mandatory = $true)][string]$ContractBindingSha256,
        [Parameter(Mandatory = $true)]$CycleState
    )
    $objectiveJson = $Objective | ConvertTo-Json -Compress
    $stageText = [string]::Join(',', $AgentStages)
    $cycleFacts = New-CycleControllerFacts -RunDirectory $RunDirectory -CycleCliPath $CycleCliPath -CycleCliSha256 $CycleCliSha256 -CyclePolicyFile $CyclePolicyFile -CyclePolicySha256 $CyclePolicySha256 -InitialTicketsFile $InitialTicketsFile -InitialTicketsSha256 $InitialTicketsSha256 -ContractBindingSha256 $ContractBindingSha256 -CycleState $CycleState
    $template = @'
# Launcher-enforced Goal continuity gate

Before doing any research, call `get_goal`. Continue only if it returns an existing Goal whose objective exactly equals the JSON string below. Do not create, replace, or silently alter the Goal. If no matching active Goal exists, return exactly `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED` as the entire final response and stop without beginning research or launching child agents.

- expected_objective_sha256: `__OBJECTIVE_SHA256__`
- expected_objective_json: __OBJECTIVE_JSON__

# Launcher-enforced execution facts

- configured_child_agent_cap: __CHILD_CAP__
- possible_configured_total_including_root: __TOTAL_CAP__
- adaptive_child_agent_stages: __AGENT_STAGES__
- total_round_budget: __TOTAL_ROUND_BUDGET__
- attempt_budget: __ATTEMPT_BUDGET__
- audit_interval_attempts: __AUDIT_INTERVAL_ATTEMPTS__
- round_budget_enforcement: cycle_controller
- max_runtime_minutes_per_research_exec_segment: __MAX_RUNTIME_MINUTES__
- web_search: __WEB_SEARCH__

# Launcher-enforced cycle-controller gate

The launcher verified the following JSON immediately before this turn. The CLI path is absolute and its SHA-256 is pinned. Use only that CLI to mutate cycle state; do not edit ledger files directly.

- only_allowed_initial_substantive_cycle_action: AttemptStart for exactly one registered ticket (read-only Status/Verify is also permitted)

```json
__CYCLE_FACTS__
```

Every mathematical attempt must begin with a successful `AttemptStart` and end with the matching `AttemptEnd`. Splitting, merging, or renaming work does not avoid an `ATTEMPT_START`; the controller is the budget authority. Scheduled audits are based on `attempts_since_last_audit`, which resets only after a valid `AuditEnd`; global attempt count never resets. When an audit is due, complete the controller-gated audit before another attempt. Before returning, invoke the CLI `ReturnCheck`; the launcher independently requires a clean return and checkpoints the verified ledger state.

Treat these facts as authoritative if later prose conflicts. A zero runtime value means that the launcher imposes no hard wall-clock timeout on this exec segment.

# Approved execution prompt

__PROMPT_TEXT__
'@
    $result = $template.Replace('__OBJECTIVE_SHA256__', $ObjectiveSha256).Replace('__OBJECTIVE_JSON__', $objectiveJson)
    $result = $result.Replace('__CHILD_CAP__', [string]$MaxChildAgents).Replace('__TOTAL_CAP__', [string]($MaxChildAgents + 1)).Replace('__AGENT_STAGES__', $stageText)
    $result = $result.Replace('__TOTAL_ROUND_BUDGET__', [string]$TotalRoundBudget).Replace('__ATTEMPT_BUDGET__', [string]$AttemptBudget).Replace('__AUDIT_INTERVAL_ATTEMPTS__', [string]$AuditIntervalAttempts)
    $result = $result.Replace('__MAX_RUNTIME_MINUTES__', [string]$MaxRuntimeMinutes).Replace('__WEB_SEARCH__', $WebSearch).Replace('__CYCLE_FACTS__', $cycleFacts)
    return $result.Replace('__PROMPT_TEXT__', $PromptText)
}

function New-CycleContinuationTurnPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Objective,
        [Parameter(Mandatory = $true)][string]$ObjectiveSha256,
        [Parameter(Mandatory = $true)][string]$ContinuationText,
        [Parameter(Mandatory = $true)][ValidateRange(1, 16)][int]$MaxChildAgents,
        [Parameter(Mandatory = $true)][int[]]$AgentStages,
        [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$TotalRoundBudget,
        [Parameter(Mandatory = $true)][ValidateRange(0, 2147483647)][int]$AttemptBudget,
        [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$AuditIntervalAttempts,
        [Parameter(Mandatory = $true)][ValidateRange(0, 525600)][int]$MaxRuntimeMinutes,
        [Parameter(Mandatory = $true)][ValidateSet('allowed', 'denied')][string]$WebSearch,
        [Parameter(Mandatory = $true)][string]$RunDirectory,
        [Parameter(Mandatory = $true)][string]$CycleCliPath,
        [Parameter(Mandatory = $true)][string]$CycleCliSha256,
        [Parameter(Mandatory = $true)][string]$CyclePolicyFile,
        [Parameter(Mandatory = $true)][string]$CyclePolicySha256,
        [Parameter(Mandatory = $true)][string]$InitialTicketsFile,
        [Parameter(Mandatory = $true)][string]$InitialTicketsSha256,
        [Parameter(Mandatory = $true)][string]$ContractBindingSha256,
        [Parameter(Mandatory = $true)]$CycleState,
        [Parameter(Mandatory = $true)][ValidateSet('normal', 'recovery_or_audit_only')][string]$ResumeMode
    )
    $objectiveJson = $Objective | ConvertTo-Json -Compress
    $stageText = [string]::Join(',', $AgentStages)
    $cycleFacts = New-CycleControllerFacts -RunDirectory $RunDirectory -CycleCliPath $CycleCliPath -CycleCliSha256 $CycleCliSha256 -CyclePolicyFile $CyclePolicyFile -CyclePolicySha256 $CyclePolicySha256 -InitialTicketsFile $InitialTicketsFile -InitialTicketsSha256 $InitialTicketsSha256 -ContractBindingSha256 $ContractBindingSha256 -CycleState $CycleState
    $allowedInitialAction = if ($null -ne $CycleState.ActiveAttempt) {
        'AttemptEnd for the same active attempt, with Outcome failed or abandoned; no other state mutation is allowed first'
    }
    elseif ($null -ne $CycleState.ActiveAudit) {
        'AuditEnd for the same active audit; no other state mutation is allowed first'
    }
    elseif ($null -ne $CycleState.AuditDue -and [bool]$CycleState.AuditDue) {
        'AuditStart for the due gate; no AttemptStart is allowed'
    }
    elseif ($ResumeMode -eq 'recovery_or_audit_only') {
        'AuditStart for recovery or closing; no AttemptStart is allowed'
    }
    else {
        'one controller-authorized AttemptStart, unless the controller requires an audit gate first'
    }
    $recoveryRule = if ($ResumeMode -eq 'recovery_or_audit_only') {
        'The verified state is dirty. Do not perform the requested continuation, start a new attempt, or do new mathematics. Use only controller-permitted recovery actions: close the same active attempt as failed/abandoned if one exists, complete the same active audit if one exists, otherwise start and complete the required recovery audit. Finish with ReturnCheck. Report only recovery/audit results.'
    }
    else {
        'The verified state is clean. You may execute the continuation only through controller-authorized AttemptStart/AttemptEnd and AuditStart/AuditEnd transitions.'
    }
    $template = @'
# Launcher-enforced continuation gate

Before continuing, call `get_goal`. Continue only if the active Goal objective exactly equals the JSON string below. Do not recreate or alter the Goal. Do not reconstruct or re-inject the initial orchestration prompt. If the Goal or frozen contract is missing or mismatched, return exactly `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED` and stop.

- expected_objective_sha256: `__OBJECTIVE_SHA256__`
- expected_objective_json: __OBJECTIVE_JSON__

# Frozen execution facts for this continuation

- configured_child_agent_cap: __CHILD_CAP__
- possible_configured_total_including_root: __TOTAL_CAP__
- adaptive_child_agent_stages: __AGENT_STAGES__
- original_total_round_budget: __TOTAL_ROUND_BUDGET__
- original_attempt_budget: __ATTEMPT_BUDGET__
- audit_interval_attempts: __AUDIT_INTERVAL_ATTEMPTS__
- budgets_must_not_reset_on_resume: true
- round_budget_enforcement: cycle_controller
- resume_cycle_mode: __RESUME_MODE__
- only_allowed_initial_substantive_cycle_action: __ALLOWED_INITIAL_ACTION__
- max_runtime_minutes_for_this_resume_exec_segment: __MAX_RUNTIME_MINUTES__
- web_search: __WEB_SEARCH__

# Launcher-enforced cycle-controller gate

The launcher verified this state immediately before the turn. The CLI path is absolute and its SHA-256 is pinned. Use only that CLI to mutate state; never edit ledger files directly.

```json
__CYCLE_FACTS__
```

__RECOVERY_RULE__

Attempt accounting is global and cannot be evaded by splitting, merging, or renaming work. Scheduled gates use `attempts_since_last_audit`; only a valid `AuditEnd` resets that counter. Invoke `ReturnCheck` before returning; the launcher independently requires a clean return and checkpoints the verified ledger state.

# Approved continuation instruction

__CONTINUATION_TEXT__
'@
    $result = $template.Replace('__OBJECTIVE_SHA256__', $ObjectiveSha256).Replace('__OBJECTIVE_JSON__', $objectiveJson)
    $result = $result.Replace('__CHILD_CAP__', [string]$MaxChildAgents).Replace('__TOTAL_CAP__', [string]($MaxChildAgents + 1)).Replace('__AGENT_STAGES__', $stageText)
    $result = $result.Replace('__TOTAL_ROUND_BUDGET__', [string]$TotalRoundBudget).Replace('__ATTEMPT_BUDGET__', [string]$AttemptBudget).Replace('__AUDIT_INTERVAL_ATTEMPTS__', [string]$AuditIntervalAttempts)
    $result = $result.Replace('__RESUME_MODE__', $ResumeMode).Replace('__ALLOWED_INITIAL_ACTION__', $allowedInitialAction).Replace('__MAX_RUNTIME_MINUTES__', [string]$MaxRuntimeMinutes).Replace('__WEB_SEARCH__', $WebSearch)
    $result = $result.Replace('__CYCLE_FACTS__', $cycleFacts).Replace('__RECOVERY_RULE__', $recoveryRule)
    return $result.Replace('__CONTINUATION_TEXT__', $ContinuationText)
}

function Test-ProcessIdentityFromManifest {
    param($ProcessRecord)
    if ($null -eq $ProcessRecord -or $null -eq $ProcessRecord.pid -or $null -eq $ProcessRecord.start_time_utc) { return $false }
    $process = Get-Process -Id ([int]$ProcessRecord.pid) -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $false }
    try {
        $expectedStart = [DateTime]::Parse([string]$ProcessRecord.start_time_utc, $null, [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
        $actualStart = $process.StartTime.ToUniversalTime()
        if ([Math]::Abs(($expectedStart - $actualStart).TotalMilliseconds) -gt 250) { return $false }
        if ($ProcessRecord.executable_path -and -not $process.Path.Equals([string]$ProcessRecord.executable_path, [StringComparison]::OrdinalIgnoreCase)) { return $false }
        return $true
    }
    catch { return $false }
}

Export-ModuleMember -Function @(
    'Assert-PowerShell7', 'Get-UtcNowString', 'Get-Sha256HexFromBytes', 'Get-Sha256HexFromText',
    'Get-Sha256HexFromFile', 'Test-FixedTimeHexEqual', 'Assert-LocalAbsolutePath',
    'Assert-NoReparsePointChain', 'Test-PathInsideDirectory', 'Get-ResearchRunsRoot', 'Get-ResearchProjectsRoot',
    'Resolve-ResearchRunContext', 'Resolve-ResearchRunDirectory', 'Resolve-RunInputFile', 'Assert-FreshRunDirectory',
    'Read-StrictUtf8File', 'Write-Utf8FileNew', 'ConvertTo-CanonicalJson', 'Get-ManifestKeyPath',
    'Get-ManifestKey', 'Write-AtomicText', 'Write-SignedJsonPayload', 'Read-SignedJsonPayload',
    'Get-MutexName', 'Enter-NamedLease', 'Exit-NamedLease', 'Open-RunLeaseFile',
    'Get-SanitizedEnvironment', 'Get-TrustedLocalAppData', 'Get-CodexBinRoot', 'Get-CodexCandidatePaths',
    'Get-OpenAIExecutableAttestation', 'Assert-AttestationStillValid', 'Start-AttestedProcess',
    'Stop-AttestedProcessHandle', 'Invoke-ShortAttestedProcess', 'Select-TrustedCodexExecutable',
    'Get-AgentStages', 'Parse-PromptV4Metadata', 'Parse-PromptV5Metadata', 'Parse-PromptV6Metadata', 'Get-ProjectIdentitySha256', 'Test-PromptMetadataAgainstParameters',
    'Assert-ContinuationInstruction',
    'ConvertTo-TomlBasicString', 'New-CodexGlobalArguments', 'New-CodexExecArguments',
    'New-CodexFeaturesArguments', 'Test-CodexFeaturePreflightOutput', 'Read-CodexJsonLog',
    'New-GoalBootstrapPrompt', 'New-GoalOutputSchema', 'Test-GoalReadyMarker',
    'New-ResearchTurnPrompt', 'New-ContinuationTurnPrompt', 'New-CycleControllerFacts',
    'New-CycleResearchTurnPrompt', 'New-CycleContinuationTurnPrompt', 'Test-ProcessIdentityFromManifest'
)
