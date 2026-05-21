param(
    [switch]$SkipDocker,
    [switch]$SkipInstall,
    [switch]$SkipMigrations
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Import-EnvFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $Line = $_.Trim()
        if (-not $Line -or $Line.StartsWith("#")) {
            return
        }
        if ($Line -match "^([^#=]+)=(.*)$") {
            $Name = $matches[1].Trim()
            $Value = $matches[2].Trim()
            if (($Value.StartsWith('"') -and $Value.EndsWith('"')) -or ($Value.StartsWith("'") -and $Value.EndsWith("'"))) {
                $Value = $Value.Substring(1, $Value.Length - 2)
            }
            [System.Environment]::SetEnvironmentVariable($Name, $Value, "Process")
        }
    }
}

if (-not $SkipDocker) {
    & (Join-Path $Root "dev-deps.ps1")
}

if (-not (Test-Path $VenvPython)) {
    Set-Location $BackendDir
    py -3.13 -m venv .venv
}

Set-Location $BackendDir

Import-EnvFile (Join-Path $BackendDir ".env")
Import-EnvFile (Join-Path $BackendDir ".env.local")

if (-not $SkipInstall) {
    & $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

if (-not $SkipMigrations) {
    & $VenvPython -m alembic upgrade head
}

& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
