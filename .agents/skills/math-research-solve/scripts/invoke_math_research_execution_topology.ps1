[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('access-prepare','validate-readback','validate-consumer','validate-project-consumer','go-check')][string]$Action,
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [string]$ReceiptPath,
    [string]$TicketPath,
    [string]$WorkerTopologyPath,
    [string]$PublisherTopologyPath,
    [string]$ConsumerTopologyPath,
    [string]$ExpectedConsumerPrincipal,
    [string]$ExpectedProjectHeadSha256,
    [ValidateRange(30,1800)][int]$TtlSeconds=300,
    [string]$ExpectedReceiptSha256
)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$argv=@('-B',(Join-Path $PSScriptRoot 'math_research_execution_topology.py'),$Action,'--project',$ProjectPath)
if($Action -ne 'validate-project-consumer'){
    if(-not $ReceiptPath){throw "$Action requires ReceiptPath."}
    $argv+=@('--receipt',$ReceiptPath)
}
if($Action -eq 'access-prepare'){
    if(-not $TicketPath -or -not $WorkerTopologyPath -or -not $PublisherTopologyPath -or -not $ConsumerTopologyPath -or -not $ExpectedConsumerPrincipal){throw 'access-prepare requires ticket, worker, publisher, consumer, and expected consumer principal bindings.'}
    $argv+=@('--ticket',$TicketPath,'--worker-topology',$WorkerTopologyPath,'--publisher-topology',$PublisherTopologyPath,'--consumer-topology',$ConsumerTopologyPath,'--expected-consumer-principal',$ExpectedConsumerPrincipal,'--ttl-seconds',[string]$TtlSeconds)
}elseif($Action -eq 'validate-readback'){
    if(-not $PublisherTopologyPath){throw 'validate-readback requires PublisherTopologyPath.'}
    $argv+=@('--publisher-topology',$PublisherTopologyPath)
}elseif($Action -eq 'validate-consumer'){
    if(-not $ConsumerTopologyPath){throw 'validate-consumer requires ConsumerTopologyPath.'}
    $argv+=@('--consumer-topology',$ConsumerTopologyPath)
}elseif($Action -eq 'validate-project-consumer'){
    if(-not $ConsumerTopologyPath -or -not $ExpectedConsumerPrincipal -or -not $ExpectedProjectHeadSha256){throw 'validate-project-consumer requires consumer topology, expected principal, and expected project head hash.'}
    $argv+=@('--consumer-topology',$ConsumerTopologyPath,'--expected-consumer-principal',$ExpectedConsumerPrincipal,'--expected-project-head-sha256',$ExpectedProjectHeadSha256)
}else{
    if(-not $ExpectedReceiptSha256){throw 'go-check requires ExpectedReceiptSha256.'}
    $argv+=@('--expected-receipt-sha256',$ExpectedReceiptSha256)
}
& python @argv
exit $LASTEXITCODE
