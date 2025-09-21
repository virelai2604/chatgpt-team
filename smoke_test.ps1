# BIFL SMOKE TEST
$logPath = 'C:\Users\User\Desktop\run result.txt'
Clear-Content -LiteralPath $logPath

function Log($msg) {
  $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  Add-Content -LiteralPath $logPath -Value "[$ts] $msg"
}

# -------------------------------
# 1. GET /v1/models
Log "🔍 Testing GET /v1/models"
try {
  Invoke-WebRequest -Uri "https://chatgpt-team.pages.dev/v1/models" -Headers @{
    Authorization = "Bearer $env:OPENAI_KEY"
    "OpenAI-Org"  = "$env:OPENAI_ORG_ID"
  } -UseBasicParsing | Tee-Object -Append $logPath
} catch {
  Log "❌ /v1/models failed: $_"
}

# -------------------------------
# 2. POST /v1/responses
Log "💬 Testing POST /v1/responses"
$body = @{
  model = "gpt-4"
  input = @(@{ role = "user"; content = "Return this message in JSON." })
} | ConvertTo-Json -Depth 10
try {
  Invoke-WebRequest -Uri "https://chatgpt-team.pages.dev/v1/responses" -Method POST `
    -Body $body -ContentType "application/json" -Headers @{
      Authorization = "Bearer $env:OPENAI_KEY"
      "OpenAI-Org" = "$env:OPENAI_ORG_ID"
    } -UseBasicParsing | Tee-Object -Append $logPath
} catch {
  Log "❌ /v1/responses failed: $_"
}

# -------------------------------
# 3. POST /v1/files (multipart)
Log "📤 Testing POST /v1/files upload"

$tempFile = "$env:TEMP\sample.txt"
"Test file upload content" | Set-Content -Path $tempFile -Encoding UTF8

try {
  $form = @{
    file    = Get-Item $tempFile
    purpose = "fine-tune"
  }

  Invoke-WebRequest -Uri "https://chatgpt-team.pages.dev/v1/files" -Method POST `
    -Form $form -Headers @{
      Authorization = "Bearer $env:OPENAI_KEY"
      "OpenAI-Org" = "$env:OPENAI_ORG_ID"
    } -UseBasicParsing | Tee-Object -Append $logPath
} catch {
  Log "❌ /v1/files failed: $_"
}

# -------------------------------
# 4. GET /v1/assistants
Log "🧠 Testing GET /v1/assistants"
try {
  Invoke-WebRequest -Uri "https://chatgpt-team.pages.dev/v1/assistants" -Headers @{
    Authorization = "Bearer $env:OPENAI_KEY"
    "OpenAI-Org" = "$env:OPENAI_ORG_ID"
  } -UseBasicParsing | Tee-Object -Append $logPath
} catch {
  Log "❌ /v1/assistants failed: $_"
}

# -------------------------------
# 5. GET /v1/health
Log "🩺 Testing GET /v1/health"
try {
  Invoke-WebRequest -Uri "https://chatgpt-team.pages.dev/v1/health" `
    -UseBasicParsing | Tee-Object -Append $logPath
} catch {
  Log "❌ /v1/health failed: $_"
}

Log "🧪 WS: /v1/realtime test"
try {
  Push-Location "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\worker"
  node .\test_realtime.mjs | Tee-Object -Append $logPath
  Pop-Location
  Log "✅ WS test passed"
} catch {
  Log "❌ WS test failed: $_"
}
