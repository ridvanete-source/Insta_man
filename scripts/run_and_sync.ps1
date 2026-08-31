Set-Location "D:\Claude_project\instagram_bot"

$logDir = "D:\Claude_project\instagram_bot\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir "run_and_sync.log"

function Write-Log {
    param([string]$Message)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message" | Add-Content -Path $logFile -Encoding utf8
}

Write-Log "=== run started ==="

git pull --rebase --autostash *>> $logFile
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR git pull exit=$LASTEXITCODE"
    exit $LASTEXITCODE
}

& ".venv\Scripts\python.exe" -m insta_man.cli run *>> $logFile
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR insta_man.cli run exit=$LASTEXITCODE"
    exit $LASTEXITCODE
}

git add content_library/queue.yaml
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "chore: update queue status (local run) [skip ci]" *>> $logFile
    git push *>> $logFile
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR git push exit=$LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

Write-Log "=== run finished OK ==="
