$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

& (Join-Path $Root "dev-deps.ps1")

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $Root "dev-backend.ps1"),
    "-SkipDocker"
)

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $Root "dev-frontend.ps1"),
    "-SkipDocker"
)
