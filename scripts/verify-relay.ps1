Set-Location -LiteralPath "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team"

$baseUrl = "https://chatgpt-team.pages.dev/v1"
$resultFile = "$env:USERPROFILE\Desktop\run result.txt"
$apiKey = $env:OPENAI_API_KEY

$headers = @{
  "Authorization"    = "Bearer $apiKey"
  "OpenAI-Org"       = "org-BE0YNlrYbCShFGQxMkW2f0fU"
  "OpenAI-Project"   = "proj_sZ0J3FtvBLrNJic6pXlx56Mm"
}

"TEST ➤ /v1/health" | Tee-Object -FilePath $resultFile
try {
  $health = Invoke-RestMethod "$baseUrl/health" -TimeoutSec 10
  if ($health.ok) {
    "✅ PASSED" | Tee-Object -Append $resultFile
  } else {
    "❌ Failed: $($health | ConvertTo-Json -Depth 4)" | Tee-Object -Append $resultFile
  }
} catch { "❌ Health Exception: $_" | Tee-Object -Append $resultFile }

"TEST ➤ /v1/models" | Tee-Object -Append $resultFile
try {
  $models = Invoke-RestMethod "$baseUrl/models" -Headers $headers -TimeoutSec 10
  "✅ Models: $($models.data.Count)" | Tee-Object -Append $resultFile
} catch { "❌ Models Exception: $_" | Tee-Object -Append $resultFile }

"TEST ➤ completions (non-stream)" | Tee-Object -Append $resultFile
$chat = @{
  model = "gpt-4"
  messages = @(@{ role = "user"; content = "Hello!" })
  stream = $false
} | ConvertTo-Json -Depth 6

try {
  $resp = Invoke-RestMethod "$baseUrl/chat/completions" -Method POST -Headers $headers -Body $chat -ContentType "application/json" -TimeoutSec 15
  $text = $resp.choices[0].message.content
  "✅ Chat: $text" | Tee-Object -Append $resultFile
} catch { "❌ Chat error: $_" | Tee-Object -Append $resultFile }

"TEST ➤ completions (streaming)" | Tee-Object -Append $resultFile
$chatStream = $chat -replace '"stream":false', '"stream":true'

try {
  Invoke-WebRequest "$baseUrl/chat/completions" -Method POST -Headers $headers -Body $chatStream -ContentType "application/json" | Out-Null
  "✅ Stream test OK" | Tee-Object -Append $resultFile
} catch { "❌ Stream error: $_" | Tee-Object -Append $resultFile }

"✅ Done > $resultFile"
