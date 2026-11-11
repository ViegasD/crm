function Import-ScriptsEnv {
    param([string]$Path = (Join-Path $PSScriptRoot ".env"))

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        if ($line -match '^([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
        }
    }
}

function Resolve-ClickUpConfig {
    param(
        [string]$ApiToken,
        [string]$FolderId
    )

    Import-ScriptsEnv

    $resolvedToken = if ($ApiToken) { $ApiToken } else { $env:CLICKUP_API_TOKEN }
    $resolvedFolderId = if ($FolderId) { $FolderId } else { $env:CLICKUP_FOLDER_ID }

    if (-not $resolvedToken) {
        throw "ClickUp API token not provided. Set CLICKUP_API_TOKEN in scripts/.env or pass -ApiToken."
    }

    return @{
        ApiToken = $resolvedToken
        FolderId = $resolvedFolderId
        Headers = @{
            Authorization = $resolvedToken
            "Content-Type" = "application/json"
        }
    }
}

function Invoke-ClickUpGet {
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][hashtable]$Headers
    )

    Invoke-RestMethod -Method Get -Uri $Uri -Headers $Headers
}

function ConvertTo-ComparableTaskName {
    param([string]$Value)

    if (-not $Value) {
        return ""
    }

    $normalized = $Value.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder

    foreach ($char in $normalized.ToCharArray()) {
        $category = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($category -eq [Globalization.UnicodeCategory]::NonSpacingMark) {
            continue
        }

        [void]$builder.Append($char)
    }

    $collapsed = $builder.ToString() -replace '[^a-z0-9]+', ' '
    return ($collapsed -replace '\s+', ' ').Trim()
}

function Find-ClickUpTask {
    param(
        [Parameter(Mandatory)][array]$Tasks,
        [string]$TaskId,
        [string]$TaskName
    )

    if ($TaskId) {
        return $Tasks | Where-Object { $_.id -eq $TaskId } | Select-Object -First 1
    }

    if ($TaskName) {
        $target = ConvertTo-ComparableTaskName -Value $TaskName

        $exact = $Tasks | Where-Object {
            (ConvertTo-ComparableTaskName -Value $_.name) -eq $target
        } | Select-Object -First 1

        if ($exact) {
            return $exact
        }

        return $Tasks | Where-Object {
            $candidate = ConvertTo-ComparableTaskName -Value $_.name
            $candidate.Contains($target) -or $target.Contains($candidate)
        } | Select-Object -First 1
    }

    throw "Each update item must provide taskId or taskName."
}