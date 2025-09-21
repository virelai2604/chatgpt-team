function Log($msg) {
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Output ("[{0}] $msg" -f $timestamp)
}

Log "🧪 /v1/health"
try {
  $resp = Invoke-RestMethod -Uri "https://chatgpt-team.pages.dev/v1/health"
  Log "✅ Health: $($resp.status)"
} catch {
  Log "❌ Health failed: $_"
}

Log "🧪 /v1/models"
try {
  $resp = Invoke-RestMethod -Uri "https://chatgpt-team.pages.dev/v1/models"
  Log "✅ Models: $($resp.data.Count) models"
} catch {
  Log "❌ Models failed: $_"
}

Log "🧪 /v1/assistants"
try {
  $resp = Invoke-RestMethod -Uri "https://chatgpt-team.pages.dev/v1/assistants"
  Log "✅ Assistants: success"
} catch {
  Log "❌ Assistants failed: $_"
}

Log "🧪 WebSocket: test_realtime.mjs"
try {
  Push-Location "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\worker"
  node .\test_realtime.mjs
  Pop-Location
  Log "✅ WS test passed"
} catch {
  Log "❌ WS test failed: $_"
}

Log "🧪 WSS direct (curl)"
try {
  curl --include -N `
    -H "Connection: Upgrade" `
    -H "Upgrade: websocket" `
    -H "Sec-WebSocket-Key: SGVsbG9Xb3JsZA==" `
    -H "Sec-WebSocket-Version: 13" `
    "https://chatgpt-team-realtime.virelai.workers.dev/v1/realtime"
  Log "✅ WSS curl test passed"
} catch {
  Log "❌ WSS curl test failed"
}

Write-Output "[WSS] 🔍 WebSocket 1-on-1 Echo Test (max 5s)..."

try {
  $uri = "wss://chatgpt-team-realtime.virelai.workers.dev/v1/realtime"
  $client = New-Object System.Net.WebSockets.ClientWebSocket
  $ct = [Threading.CancellationToken]::None

  # Connect
  $client.ConnectAsync($uri, $ct).Wait(5000)

  if ($client.State -ne 'Open') {
    Write-Output "[WSS] ❌ WebSocket failed to open"
    return
  }

  Write-Output "[WSS] ✅ WebSocket connected"

  # Send "ping" message
  $json = '{"type":"ping"}'
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
  $sendBuffer = New-Object System.ArraySegment[byte] -ArgumentList (, $bytes)
  $client.SendAsync($sendBuffer, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).Wait()

  # Receive response
  $recvBuffer = New-Object byte[] 1024
  $segment = New-Object System.ArraySegment[byte] -ArgumentList (, $recvBuffer)
  $task = $client.ReceiveAsync($segment, $ct)
  $task.Wait(5000)

  if ($task.IsCompleted) {
    $len = $task.Result.Count
    $response = [System.Text.Encoding]::UTF8.GetString($recvBuffer, 0, $len)
    Write-Output "[WSS] ✅ Received echo: $response"
  } else {
    Write-Output "[WSS] ❌ No response within 5s"
  }

  # Close cleanly
  $client.Dispose()
} catch {
  Write-Output "[WSS] ❌ Exception: $($_.Exception.Message)"
}