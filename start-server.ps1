# ChatGPT Team Server Launcher
$pythonPath = "C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe"
$projectPath = "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team"

Write-Host "🚀 Starting ChatGPT Team Indonesia Server..." -ForegroundColor Cyan
Write-Host "📁 Project: $projectPath" -ForegroundColor Yellow
Write-Host "🌐 URL: http://localhost:8000" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Gray

Set-Location $projectPath
& $pythonPath -m http.server 8000
