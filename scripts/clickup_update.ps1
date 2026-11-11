param(
    [string]$ApiToken,
    [string]$PlanPath = (Join-Path $PSScriptRoot "clickup_update_plan.local.json")
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "clickup_common.ps1")

$config = Resolve-ClickUpConfig -ApiToken $ApiToken
$headers = $config.Headers

if (-not (Test-Path $PlanPath)) {
    throw "Update plan file not found: $PlanPath"
}

$plan = Get-Content $PlanPath -Raw | ConvertFrom-Json

if (-not $plan.updates -or $plan.updates.Count -eq 0) {
    throw "No updates found in $PlanPath"
}

foreach ($update in $plan.updates) {
    if (-not $update.listId) {
        throw "Each update item must provide listId."
    }

    $tasks = @(Invoke-ClickUpGet -Uri "https://api.clickup.com/api/v2/list/$($update.listId)/task?include_closed=true" -Headers $headers).tasks
    $task = Find-ClickUpTask -Tasks $tasks -TaskId $update.taskId -TaskName $update.taskName

    if (-not $task) {
        throw "Task not found in list $($update.listId): $($update.taskName)$($update.taskId)"
    }

    if ($update.status) {
        $body = @{ status = $update.status } | ConvertTo-Json
        Invoke-RestMethod -Method Put -Uri "https://api.clickup.com/api/v2/task/$($task.id)" -Headers $headers -Body $body | Out-Null
        Write-Host "STATUS $($task.name) -> $($update.status)"
    }

    if ($update.comment) {
        $commentBody = @{ comment_text = $update.comment } | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri "https://api.clickup.com/api/v2/task/$($task.id)/comment" -Headers $headers -Body $commentBody | Out-Null
        Write-Host "COMMENT $($task.name)"
    }
}