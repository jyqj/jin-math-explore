#!/usr/bin/env python3
"""Dependency-free process identity binding for safe control operations."""

from __future__ import annotations

import ctypes
import hashlib
import os
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Any


class ProcessIdentityError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _windows_snapshot(pid: int) -> tuple[str, Path]:
    query = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(query, False, pid)
    if not handle:
        raise ProcessIdentityError("process is unavailable")
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            raise ProcessIdentityError("process executable path is unavailable")
        creation = wintypes.FILETIME(); exit_time = wintypes.FILETIME()
        kernel = wintypes.FILETIME(); user = wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
            raise ProcessIdentityError("process creation time is unavailable")
        ticks = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        return f"windows-filetime:{ticks}", Path(buffer.value)
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _linux_snapshot(pid: int) -> tuple[str, Path]:
    root = Path("/proc") / str(pid)
    try:
        stat_text = (root / "stat").read_text(encoding="ascii")
        close = stat_text.rfind(")")
        if close < 0:
            raise ProcessIdentityError("process stat shape is invalid")
        fields = stat_text[close + 2:].split()
        if len(fields) <= 19:
            raise ProcessIdentityError("process stat is incomplete")
        if fields[0] == "Z":
            raise ProcessIdentityError("process has exited")
        start_ticks = fields[19]
        executable = Path(os.readlink(root / "exe"))
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError) as exc:
        raise ProcessIdentityError("process identity is unavailable") from exc
    return f"linux-startticks:{start_ticks}", executable


class _DarwinBsdInfo(ctypes.Structure):
    # Apple XNU bsd/sys/proc_info.h: struct proc_bsdinfo (MAXCOMLEN == 16).
    _fields_ = [
        ("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32),
        ("pbi_xstatus", ctypes.c_uint32), ("pbi_pid", ctypes.c_uint32),
        ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
        ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32),
        ("pbi_rgid", ctypes.c_uint32), ("pbi_svuid", ctypes.c_uint32),
        ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
        ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32),
        ("pbi_nfiles", ctypes.c_uint32), ("pbi_pgid", ctypes.c_uint32),
        ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
        ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32),
        ("pbi_start_tvsec", ctypes.c_uint64), ("pbi_start_tvusec", ctypes.c_uint64),
    ]


def _darwin_snapshot(pid: int) -> tuple[str, Path]:
    try:
        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        library.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        library.proc_pidinfo.restype = ctypes.c_int
        library.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        library.proc_pidpath.restype = ctypes.c_int
        info = _DarwinBsdInfo()
        size = ctypes.sizeof(info)
        received = library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), size)
        if received != size or info.pbi_pid != pid:
            raise ProcessIdentityError("Darwin process start identity is unavailable")
        buffer = ctypes.create_string_buffer(4096)
        length = library.proc_pidpath(pid, buffer, len(buffer))
        if length <= 0:
            raise ProcessIdentityError("Darwin process executable path is unavailable")
        executable = Path(os.fsdecode(buffer.value))
        token = f"darwin-timeval:{info.pbi_start_tvsec}:{info.pbi_start_tvusec}"
        return token, executable
    except OSError as exc:
        raise ProcessIdentityError("Darwin libproc is unavailable") from exc


def snapshot_process(pid: int) -> dict[str, Any]:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ProcessIdentityError("PID must be a positive integer")
    if os.name == "nt":
        token, executable = _windows_snapshot(pid)
        platform_name = "windows"
    elif sys.platform.startswith("linux"):
        token, executable = _linux_snapshot(pid)
        platform_name = "linux"
    elif sys.platform == "darwin":
        token, executable = _darwin_snapshot(pid)
        platform_name = "darwin"
    else:
        raise ProcessIdentityError("process identity provider is not yet available on this platform")
    executable = Path(os.path.abspath(executable))
    if not executable.is_file():
        raise ProcessIdentityError("process executable is not a regular file")
    return {
        "pid": pid,
        "platform": platform_name,
        "start_token": token,
        "executable_path": str(executable),
        "executable_sha256": sha256_file(executable),
    }


def process_identity_matches(record: Any) -> bool:
    if not isinstance(record, dict) or set(record) != {"pid", "platform", "start_token", "executable_path", "executable_sha256"}:
        return False
    try:
        current = snapshot_process(record["pid"])
    except (ProcessIdentityError, OSError, ValueError, TypeError):
        return False
    path_equal = os.path.normcase(current["executable_path"]) == os.path.normcase(str(record["executable_path"]))
    return (
        current["platform"] == record["platform"]
        and current["start_token"] == record["start_token"]
        and path_equal
        and hashlib.sha256(current["executable_sha256"].encode()).digest()
        == hashlib.sha256(str(record["executable_sha256"]).encode()).digest()
    )
