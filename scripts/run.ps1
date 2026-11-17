# Run JARVIS
Set-Location $PSScriptRoot\..
$env:OLLAMA_VULKAN="false"
$env:OLLAMA_LLM_LIBRARY="cpu"
if (-not (Get-Process ollama -ErrorAction SilentlyContinue)) {
    Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden
    Start-Sleep -Seconds 3
}
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --ws-ping-interval 120 --ws-ping-timeout 120
