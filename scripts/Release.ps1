Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Edit these values for each release.
$Version = "0.1.2"
$ReleaseTag = ""
$RepositoryJsonPath = "..\MyKicadPlugins\repository.json"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$releaseScript = Join-Path $scriptRoot "New-PcmRelease.ps1"

if (-not (Test-Path $releaseScript)) {
    throw "Missing script: $releaseScript"
}

$params = @{
    Version = $Version
    GithubRepo = "jonasnic/Kicad_easyead2kicad_addon"
    RepositoryJsonPath = $RepositoryJsonPath
}

if (-not [string]::IsNullOrWhiteSpace($ReleaseTag)) {
    $params.ReleaseTag = $ReleaseTag
}

& $releaseScript @params