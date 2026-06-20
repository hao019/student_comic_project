param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$pattern = "^\s*TCP\s+127\.0\.0\.1:$Port\s+.*LISTENING\s+(\d+)"
$pids = @(
    netstat -ano |
        Select-String -Pattern $pattern |
        ForEach-Object {
            if ($_.Line -match $pattern) {
                [int]$Matches[1]
            }
        } |
        Sort-Object -Unique
)

foreach ($processId in $pids) {
    if ($processId -gt 0 -and $processId -ne $PID) {
        Write-Host "Stopping process $processId on 127.0.0.1:$Port..."
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Milliseconds 700

$python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
}
if (-not (Test-Path $python)) {
    throw "Could not find venv\Scripts\python.exe or .venv\Scripts\python.exe."
}

Write-Host "Starting FastAPI on http://127.0.0.1:$Port/"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
