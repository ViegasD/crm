param(
    [switch]$SkipDocker,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"

Set-Location $Root

if (-not $SkipDocker) {
    docker compose stop frontend | Out-Null
}

Set-Location $FrontendDir

if ((-not $SkipInstall) -and (-not (Test-Path (Join-Path $FrontendDir "node_modules")))) {
    npm install
}

& npm run dev
