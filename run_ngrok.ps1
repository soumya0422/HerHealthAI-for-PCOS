param(
    [string]$Authtoken
)

# Usage:
# .\run_ngrok.ps1 -Authtoken "YOUR_AUTHTOKEN"
# or set environment variable NGROK_AUTHTOKEN and run without args

if (-not $Authtoken) {
    # read from standard env var name if set
    $Authtoken = $env:NGROK_AUTHTOKEN
}

if (-not $Authtoken) {
    Write-Error "Ngrok authtoken not provided. Pass -Authtoken or set NGROK_AUTHTOKEN env var."
    exit 1
}

$ngrokExe = Join-Path -Path (Get-Location) -ChildPath 'ngrok.exe'
if (-not (Test-Path $ngrokExe)) {
    Write-Error "ngrok.exe not found in current directory. Download ngrok and place ngrok.exe here."
    exit 1
}

Write-Output "Registering authtoken..."
& $ngrokExe authtoken $Authtoken

Write-Output "Starting ngrok tunnel for port 8000 (backend)..."
Start-Process -NoNewWindow -FilePath $ngrokExe -ArgumentList 'http 8000' -WorkingDirectory (Get-Location)
Write-Output "ngrok started. Check ngrok console window for forwarding URL."
