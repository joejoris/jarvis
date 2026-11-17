# Setup JARVIS (Windows) — run from the repo root:  .\scripts\setup.ps1
Set-Location $PSScriptRoot\..

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path config.yaml)) {
    Copy-Item config.example.yaml config.yaml
    Write-Host "Created config.yaml — paste your FREE Groq key from https://console.groq.com/keys"
}

# Desktop shortcut → JARVIS.bat
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("$env:USERPROFILE\Desktop\JARVIS.lnk")
$lnk.TargetPath = Join-Path (Get-Location) "scripts\jarvis.bat"
$lnk.WorkingDirectory = Get-Location
$lnk.Description = "J.A.R.V.I.S. — Just A Rather Very Intelligent System"
$lnk.Save()

Write-Host ""
Write-Host "Setup complete. Edit config.yaml to add your Groq key, then double-click the Desktop shortcut or run .\scripts\run.ps1"
