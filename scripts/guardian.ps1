# Sylvia Guardian 2.0 — 每5分钟运行
# 健康标准（缺一不可）：
#   1. Sylvia claude.exe 存活
#   2. Sylvia 的 bun 子进程存活
#   3. iLink Bot API 连通（5秒超时探针）
# 任一失败则完整重启

$SYLVIA_PATH_PATTERN = '*\AppData\Roaming\Claude\claude-code\*\claude.exe'
$VBS_PATH = 'D:\sylvia_skill\start-hidden.vbs'
$logFile = 'D:\sylvia_skill\guardian.log'
$accountFile = "$env:USERPROFILE\.claude\channels\weixin\account.json"

function Log($msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Add-Content -Path $logFile -Value $line
}

# ========== 辅助函数 ==========
function Get-SylviaProcs {
    Get-Process claude -ErrorAction SilentlyContinue | Where-Object { $_.Path -like $SYLVIA_PATH_PATTERN }
}

function Get-SylviaDescendants {
    param($rootPids)
    $descendants = New-Object System.Collections.Generic.HashSet[int]
    $queue = New-Object System.Collections.Queue
    $rootPids | ForEach-Object { $queue.Enqueue($_) }
    while ($queue.Count -gt 0) {
        $curPid = $queue.Dequeue()
        [void]$descendants.Add($curPid)
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$curPid" -ErrorAction SilentlyContinue | ForEach-Object {
            if (-not $descendants.Contains([int]$_.ProcessId)) {
                $queue.Enqueue([int]$_.ProcessId)
            }
        }
    }
    return $descendants
}

function Test-iLinkApi {
    # 仅做存在性检查（token 配置 OK 即视为通）
    # 不做主动 long-poll：会和 Sylvia 的 bun 抢 API 连接池，且 long-poll 5s 超时会被误判
    if (-not (Test-Path $accountFile)) { return @{ok=$false; reason='no account file'} }
    try {
        $cfg = Get-Content $accountFile -Raw | ConvertFrom-Json
        if (-not $cfg.token) { return @{ok=$false; reason='token missing'} }
        return @{ok=$true; reason='token configured'}
    } catch {
        return @{ok=$false; reason='bad account json'}
    }
}

function Restart-Sylvia {
    Log '[RESTART] killing existing Sylvia claude.exe...'
    Get-SylviaProcs | ForEach-Object {
        try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Seconds 3

    Log '[RESTART] launching VBS...'
    Start-Process -FilePath 'wscript.exe' -ArgumentList "`"$VBS_PATH`"" -WindowStyle Hidden
    Start-Sleep -Seconds 25
}

# ========== 主流程 ==========
$need_restart = $false
$reasons = @()

# 1. Sylvia claude.exe 存在？
$sylvia = Get-SylviaProcs
if (-not $sylvia) {
    $need_restart = $true
    $reasons += 'sylvia claude missing'
} else {
    $sylviaPids = @($sylvia | Select-Object -ExpandProperty Id)
    # 取最年轻的 Sylvia 算 age
    $youngest = $sylvia | Sort-Object StartTime -Descending | Select-Object -First 1
    $ageSeconds = ((Get-Date) - $youngest.StartTime).TotalSeconds
    Log "Sylvia claude alive: PID $($sylviaPids -join ',') age=$([math]::Round($ageSeconds))s"

    # 2. bun 子进程存在？（启动宽限期 90 秒：刚启动的 Sylvia 还没生成 bun 是正常的）
    $descendants = Get-SylviaDescendants $sylviaPids
    $sylviaBuns = Get-Process bun -ErrorAction SilentlyContinue | Where-Object { $descendants.Contains($_.Id) }
    if (-not $sylviaBuns) {
        if ($ageSeconds -lt 90) {
            Log "bun missing but Sylvia age < 90s, grace period - skip"
        } else {
            $need_restart = $true
            $reasons += 'bun child missing (>90s grace)'
        }
    } else {
        Log "Sylvia bun alive: $($sylviaBuns.Count) process(es)"
    }
}

# 3. iLink API 连通性
$apiResult = Test-iLinkApi
if (-not $apiResult.ok) {
    $need_restart = $true
    $reasons += "api: $($apiResult.reason)"
}

# 决策
if ($need_restart) {
    Log "[UNHEALTHY] reasons: $($reasons -join '; ')"
    Restart-Sylvia

    # 验证重启结果
    $sylvia2 = Get-SylviaProcs
    if ($sylvia2) {
        $descendants2 = Get-SylviaDescendants @($sylvia2 | Select-Object -ExpandProperty Id)
        $buns2 = Get-Process bun -ErrorAction SilentlyContinue | Where-Object { $descendants2.Contains($_.Id) }
        if ($buns2) {
            Log "[RESTART OK] Sylvia=$($sylvia2.Id) bun=$($buns2.Count)"
        } else {
            Log "[RESTART PARTIAL] Sylvia up but bun still missing"
        }
    } else {
        Log '[RESTART FAIL] Sylvia did not come up'
    }
} else {
    Log "HEALTHY (api=$($apiResult.reason))"
}

# 最后：清理非 Sylvia 后代的 bun（VS Code 等其他 claude 启动的 bun）
$allBuns = Get-Process bun -ErrorAction SilentlyContinue
if ($allBuns) {
    $finalSylvia = Get-SylviaProcs
    if ($finalSylvia) {
        $finalDescendants = Get-SylviaDescendants @($finalSylvia | Select-Object -ExpandProperty Id)
        $killed = 0
        foreach ($bun in $allBuns) {
            if (-not $finalDescendants.Contains($bun.Id)) {
                try {
                    Stop-Process -Id $bun.Id -Force -ErrorAction SilentlyContinue
                    $killed++
                } catch {}
            }
        }
        if ($killed -gt 0) { Log "Killed $killed competing bun(s)" }
    }
}
