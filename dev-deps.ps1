param(
    [switch]$KeepAppContainers
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Set-Location $Root

docker compose up -d postgres redis minio evolution_postgres evolution

if (-not $KeepAppContainers) {
    docker compose stop backend celery_worker frontend | Out-Null
}

docker compose ps
