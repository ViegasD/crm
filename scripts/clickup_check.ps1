param(
    [string]$ApiToken,
    [string]$FolderId,
    [switch]$IncludeClosed,
    [string]$OutputJsonPath
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "clickup_common.ps1")

$config = Resolve-ClickUpConfig -ApiToken $ApiToken -FolderId $FolderId
$headers = $config.Headers
$FolderId = $config.FolderId

if (-not $FolderId) {
    throw "ClickUp folder id not provided. Set CLICKUP_FOLDER_ID in scripts/.env or pass -FolderId."
}

$folder = Invoke-ClickUpGet -Uri "https://api.clickup.com/api/v2/folder/$FolderId" -Headers $headers
$lists = Invoke-ClickUpGet -Uri "https://api.clickup.com/api/v2/folder/$FolderId/list" -Headers $headers

$result = [System.Collections.Generic.List[object]]::new()

Write-Host "Folder: $($folder.name) ($FolderId)"
Write-Host ""

foreach ($list in $lists.lists | Sort-Object name) {
    $query = if ($IncludeClosed) { "?include_closed=true" } else { "" }
    $tasksResponse = Invoke-ClickUpGet -Uri "https://api.clickup.com/api/v2/list/$($list.id)/task$query" -Headers $headers
    $tasks = @($tasksResponse.tasks)
    $closed = @($tasks | Where-Object { $_.status.status -in @("closed", "complete") }).Count
    $open = $tasks.Count - $closed

    Write-Host "LIST: $($list.name)"
    Write-Host "  Closed: $closed  Open: $open  Total: $($tasks.Count)"

    foreach ($task in $tasks | Sort-Object name) {
        $marker = if ($task.status.status -in @("closed", "complete")) { "[done]" } else { "[open]" }
        Write-Host "  $marker $($task.name)"
    }

    Write-Host ""

    $result.Add([pscustomobject]@{
        listId = $list.id
        listName = $list.name
        total = $tasks.Count
        closed = $closed
        open = $open
        tasks = @($tasks | Sort-Object name | ForEach-Object {
            [pscustomobject]@{
                id = $_.id
                name = $_.name
                status = $_.status.status
            }
        })
    }) | Out-Null
}

if ($OutputJsonPath) {
    $payload = [pscustomobject]@{
        folderId = $FolderId
        folderName = $folder.name
        generatedAt = (Get-Date).ToString("o")
        lists = $result
    }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $OutputJsonPath
    Write-Host "Wrote JSON report to $OutputJsonPath"
}