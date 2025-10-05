$BaseUrl = "http://127.0.0.1:8000"

function PrettyPrint($response) {
    try { $response | ConvertFrom-Json | ConvertTo-Json -Depth 10 }
    catch { $response }
}

Write-Host "`n🔎 1. GET /v1/health"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/health" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n💬 2. POST /v1/chat/completions (non-stream)"
try {
    $body = @{
        model = "gpt-3.5-turbo"
        messages = @(@{ role = "user"; content = "Say hello from relay!" })
        temperature = 0.2
        stream = $false
    } | ConvertTo-Json -Depth 5
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/chat/completions" -Method POST -Body $body -ContentType "application/json"
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n🌊 3. POST /v1/chat/completions (stream:true, expects SSE)"
try {
    $body = @{
        model = "gpt-3.5-turbo"
        messages = @(@{ role = "user"; content = "Stream this message." })
        temperature = 0.2
        stream = $true
    } | ConvertTo-Json -Depth 5
    $resp = Invoke-WebRequest -Uri "$BaseUrl/v1/chat/completions" -Method POST -Body $body -ContentType "application/json" -Headers @{Accept="text/event-stream"}
    $resp.Content
} catch { $_ }

Write-Host "`n🔤 4. POST /v1/completions (legacy completions)"
try {
    $body = @{
        model = "text-davinci-003"
        prompt = "Give me a short Python function."
        max_tokens = 32
        temperature = 0.4
        stream = $false
    } | ConvertTo-Json -Depth 5
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/completions" -Method POST -Body $body -ContentType "application/json"
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n📦 5. GET /v1/models"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/models" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n📂 6. GET /v1/files (list files)"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/files" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n🤖 7. GET /v1/assistants (proxy/future endpoint)"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/assistants" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n🔧 8. GET /v1/tools (proxy/future endpoint)"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/tools" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n🪢 9. GET /v1/threads (wildcard proxy test)"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/threads" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n🔮 10. GET /openai/test-proxy (optional extreme wildcard proxy)"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/openai/test-proxy" -Method GET
    PrettyPrint $resp
} catch { $_ }

Write-Host "`n✅ Done. Review results for errors or blocked endpoints."
