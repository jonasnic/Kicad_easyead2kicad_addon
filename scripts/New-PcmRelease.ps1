param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [string]$GithubRepo = "jonasnic/Kicad_easyead2kicad_addon",

    [string]$ReleaseTag,

    [string]$RepositoryJsonPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

if ([string]::IsNullOrWhiteSpace($ReleaseTag)) {
    $ReleaseTag = "v$Version"
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot

$distDir = Join-Path $repoRoot "dist"
$stageDir = Join-Path ([System.IO.Path]::GetTempPath()) ("easyeda2kicad-pcm-stage-" + [System.Guid]::NewGuid().ToString("N"))
$archiveName = "easyeda2kicad_addon-v$Version.zip"
$archivePath = Join-Path $distDir $archiveName

$metadataPath = Join-Path $repoRoot "metadata.json"
$entrypointPath = Join-Path $repoRoot "easyeda2kicad_plugin.py"
$bootstrapPath = Join-Path $repoRoot "__init__.py"
$pluginsPath = Join-Path $repoRoot "plugins"
$resourcesPath = Join-Path $repoRoot "resources"

foreach ($requiredPath in @($metadataPath, $entrypointPath, $pluginsPath, $resourcesPath)) {
    if (-not (Test-Path $requiredPath)) {
        throw "Required path is missing: $requiredPath"
    }
}

Write-Host "Cleaning previous build outputs..."
if (Test-Path $archivePath) {
    Remove-Item -Path $archivePath -Force
}
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

Write-Host "Creating PCM staging layout..."
New-Item -ItemType Directory -Path $stageDir | Out-Null
try {
    Copy-Item -Path $entrypointPath -Destination (Join-Path $stageDir "easyeda2kicad_plugin.py")
    if (Test-Path $bootstrapPath) {
        Copy-Item -Path $bootstrapPath -Destination (Join-Path $stageDir "__init__.py")
    }
    Copy-Item -Path $pluginsPath -Destination (Join-Path $stageDir "plugins") -Recurse
    Copy-Item -Path $resourcesPath -Destination (Join-Path $stageDir "resources") -Recurse

    $readmePath = Join-Path $repoRoot "README.md"
    if (Test-Path $readmePath) {
        Copy-Item -Path $readmePath -Destination (Join-Path $stageDir "README.md")
    }

    Write-Host "Pruning caches from package..."
    Get-ChildItem -Path $stageDir -Recurse -Directory -Filter "__pycache__" |
        ForEach-Object { Remove-Item -Path $_.FullName -Recurse -Force }
    Get-ChildItem -Path $stageDir -Recurse -File -Include "*.pyc", "*.pyo" |
        ForEach-Object { Remove-Item -Path $_.FullName -Force }

    Write-Host "Creating archive: $archiveName"
    Compress-Archive -Path (Join-Path $stageDir "*") -DestinationPath $archivePath -CompressionLevel Optimal

    $downloadSha256 = (Get-FileHash -Path $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $downloadSize = (Get-Item $archivePath).Length
    $installSize = (Get-ChildItem -Path $stageDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
    $downloadUrl = "https://github.com/$GithubRepo/releases/download/$ReleaseTag/$archiveName"
}
finally {
    if (Test-Path $stageDir) {
        Remove-Item -Path $stageDir -Recurse -Force
    }
}

Write-Host "Updating metadata.json..."
$metadata = Get-Content -Path $metadataPath -Raw | ConvertFrom-Json
$package = $metadata.packages[0]

$existing = @($package.versions | Where-Object { $_.version -eq $Version })
if ($existing.Count -eq 0) {
    $firstVersion = $package.versions[0]
    $newVersion = [ordered]@{
        version = $Version
        status = if ($null -ne $firstVersion.status) { $firstVersion.status } else { "development" }
        kicad_version = if ($null -ne $firstVersion.kicad_version) { $firstVersion.kicad_version } else { "6.0" }
        download_url = $downloadUrl
    }

    $updatedVersions = @($newVersion) + @($package.versions)
    $package.versions = $updatedVersions
} else {
    foreach ($v in $package.versions) {
        if ($v.version -eq $Version) {
            $v.download_url = $downloadUrl
        }
    }
}

$metadataJson = $metadata | ConvertTo-Json -Depth 100
Write-Utf8NoBom -Path $metadataPath -Content $metadataJson

$metadataSha256 = (Get-FileHash -Path $metadataPath -Algorithm SHA256).Hash.ToLowerInvariant()
$unixTimestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

if (-not [string]::IsNullOrWhiteSpace($RepositoryJsonPath) -and (Test-Path $RepositoryJsonPath)) {
    Write-Host "Updating repository.json..."
    $repository = Get-Content -Path $RepositoryJsonPath -Raw | ConvertFrom-Json
    $repository.packages.sha256 = $metadataSha256
    $repository.packages.update_timestamp = $unixTimestamp
    $repositoryJson = $repository | ConvertTo-Json -Depth 100
    Write-Utf8NoBom -Path $RepositoryJsonPath -Content $repositoryJson
}

Write-Host ""
Write-Host "Release build complete"
Write-Host "VERSION=$Version"
Write-Host "ARCHIVE_PATH=$archivePath"
Write-Host "DOWNLOAD_SHA256=$downloadSha256"
Write-Host "DOWNLOAD_SIZE=$downloadSize"
Write-Host "DOWNLOAD_URL=$downloadUrl"
Write-Host "INSTALL_SIZE=$installSize"
Write-Host "METADATA_SHA256=$metadataSha256"
Write-Host "UPDATE_TIMESTAMP=$unixTimestamp"

if ($env:GITHUB_ENV) {
    Add-Content -Path $env:GITHUB_ENV -Value "VERSION=$Version"
    Add-Content -Path $env:GITHUB_ENV -Value "ARCHIVE_PATH=$archivePath"
    Add-Content -Path $env:GITHUB_ENV -Value "DOWNLOAD_SHA256=$downloadSha256"
    Add-Content -Path $env:GITHUB_ENV -Value "DOWNLOAD_SIZE=$downloadSize"
    Add-Content -Path $env:GITHUB_ENV -Value "DOWNLOAD_URL=$downloadUrl"
    Add-Content -Path $env:GITHUB_ENV -Value "INSTALL_SIZE=$installSize"
    Add-Content -Path $env:GITHUB_ENV -Value "METADATA_SHA256=$metadataSha256"
    Add-Content -Path $env:GITHUB_ENV -Value "UPDATE_TIMESTAMP=$unixTimestamp"
}