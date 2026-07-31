$ErrorActionPreference = "Stop"
Set-Location "C:\Users\RIDVA\OneDrive\Masaüstü\inst"

git pull --rebase --autostash

& ".venv\Scripts\python.exe" -m insta_man.cli run

git add content_library/queue.yaml
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "chore: update queue status (local run) [skip ci]"
    git push
}
