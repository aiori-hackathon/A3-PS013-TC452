$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pythonExe = if ($pythonCmd) { $pythonCmd.Source } else { Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' }
if (!(Test-Path -LiteralPath $pythonExe)) { throw 'Install Python 3.12 and rerun setup.' }
& $pythonExe -c 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 required"'
if ($LASTEXITCODE) { throw 'Python 3.12 is required.' }
if (!(Test-Path '.venv/Scripts/python.exe')) { & $pythonExe -m venv .venv }
& '.venv/Scripts/python.exe' -m pip install -r src/backend/requirements-lock.txt
if ($LASTEXITCODE) { throw 'Python dependency installation failed.' }
$nodeExe = (Get-Command node -ErrorAction Stop).Source
$npmCli = Join-Path (Split-Path $nodeExe) 'node_modules/npm/bin/npm-cli.js'
if (!(Test-Path -LiteralPath $npmCli)) { throw 'Install Node.js with npm. npm-cli.js was not found beside node.exe.' }
Push-Location src/frontend
try {
    & $nodeExe $npmCli ci
    if ($LASTEXITCODE) { throw 'Frontend dependency installation failed.' }
    & $nodeExe $npmCli run build
    if ($LASTEXITCODE) { throw 'Frontend build failed.' }
} finally { Pop-Location }
Write-Host 'Setup complete. Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1'
