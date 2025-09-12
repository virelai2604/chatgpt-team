<#  Relay Smoke - BIFL grade (no external deps)
    Skips Moderations by request.
#>

$ErrorActionPreference = 'Stop'

# ---- Config ----
$BASE = if ($env:RELAY_BASE) { $env:RELAY_BASE.TrimEnd('/') } else { "https://chatgpt-team.pages.dev/v1" }
$KEY  = $env:OPENAI_API_KEY
if (-not $KEY) { throw "OPENAI_API_KEY is not set." }

$JsonHeaders = @{ Authorization = "Bearer $KEY"; "Content-Type" = "application/json" }

# For Assistants v2 + Vector Stores list
$BetaHeaders = $JsonHeaders.Clone()
$BetaHeaders["OpenAI-Beta"] = "assistants=v2"

# Workspace
$WorkDir = Join-Path $PSScriptRoot ".out"
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$TtsPath = Join-Path $WorkDir "tts.mp3"
$PngPath = Join-Path $WorkDir "image.png"
$TxtPath = Join-Path $WorkDir "hello.txt"
"hello from CI $(Get-Date -Format s)" | Set-Content -Encoding UTF8 $TxtPath

# ---- Helpers ----
function Invoke-Json {
  param([string]$Method="GET",[string]$Path,[hashtable]$Body,[hashtable]$Headers=$JsonHeaders)
  $uri = "$BASE$Path"
  if ($Body) { $payload = ($Body | ConvertTo-Json -Depth 12) }
  if ($Body) { (Invoke-WebRequest -Method $Method -Uri $uri -Headers $Headers -Body $payload).Content | ConvertFrom-Json }
  else       { (Invoke-WebRequest -Method $Method -Uri $uri -Headers $Headers).Content | ConvertFrom-Json }
}

function Test-Step {
  param([string]$Name,[ScriptBlock]$Script)
  $result = [ordered]@{ Name=$Name; Status="✅"; Notes="" }
  try { & $Script | Out-Null }
  catch {
    $result.Status = "❌"
    $result.Notes  = $_.Exception.Message
  }
  [pscustomobject]$result
}

# Strongly-typed list is fine; Add(T) returns void in PS so assign to $null
$results = New-Object System.Collections.Generic.List[object]

# ---- 1) Models ----
$null = $results.Add( (Test-Step -Name "Models: GET /models" -Script {
  $m = Invoke-Json -Path "/models"
  if (-not $m.data -or -not $m.data[0].id) { throw "No models listed." }
}) )

# Choose default models dynamically
function Get-ModelId {
  param([string]$contains)
  $models = (Invoke-Json -Path "/models").data
  ($models | Where-Object { $_.id -like "*$contains*" } | Select-Object -First 1 -ExpandProperty id), $models
}
$chatModel, $all = Get-ModelId -contains "gpt-4o-mini"
if (-not $chatModel) { $chatModel = "gpt-4o-mini" }
$embedModel = ($all | Where-Object { $_.id -like "text-embedding-3-*" } | Select-Object -First 1 -ExpandProperty id)
if (-not $embedModel) { $embedModel = "text-embedding-3-small" }

# ---- 2) Chat Completions ----
$null = $results.Add( (Test-Step -Name "Chat: POST /chat/completions" -Script {
  $r = Invoke-Json -Method POST -Path "/chat/completions" -Body @{
    model = $chatModel
    messages = @(@{ role="user"; content="Say pong" })
    max_tokens = 8
  }
  if (-not $r.choices[0].message.content) { throw "No content in response." }
}) )

# ---- 3) Embeddings ----
$null = $results.Add( (Test-Step -Name "Embeddings: POST /embeddings" -Script {
  $r = Invoke-Json -Method POST -Path "/embeddings" -Body @{
    model = $embedModel
    input = "hello world"
  }
  if (-not $r.data[0].embedding) { throw "No vector returned." }
}) )

# ---- 4) Responses (unified) ----
$null = $results.Add( (Test-Step -Name "Responses: POST /responses" -Script {
  $r = Invoke-Json -Method POST -Path "/responses" -Body @{
    model = $chatModel
    input = "ping"
  }
  if (-not $r.id -or $r.object -ne "response") { throw "Unexpected Responses schema." }
}) )

# ---- 5) Images (b64 -> file) ----
$null = $results.Add( (Test-Step -Name "Images: POST /images (b64_json)" -Script {
  $r = Invoke-Json -Method POST -Path "/images" -Body @{
    model = "gpt-image-1"
    prompt = "a minimalist koi logo"
    size = "512x512"
    response_format = "b64_json"
  }
  $b64 = $r.data[0].b64_json
  if (-not $b64) { throw "No image b64_json." }
  [IO.File]::WriteAllBytes($PngPath, [Convert]::FromBase64String($b64))
}) )

# ---- 6) Audio TTS (bytes -> mp3 file) ----
$null = $results.Add( (Test-Step -Name "Audio TTS: POST /audio/speech" -Script {
  $payload = @{
    model = "gpt-4o-mini-tts"
    input = "Halo dari Jakarta, ini uji TTS."
    voice = "alloy"
    format = "mp3"
  } | ConvertTo-Json -Depth 10
  Invoke-WebRequest -Method POST -Uri "$BASE/audio/speech" -Headers $JsonHeaders -Body $payload -OutFile $TtsPath | Out-Null
  if (-not (Test-Path $TtsPath)) { throw "No TTS file written." }
}) )

# ---- 7) Audio STT (use TTS output as input) ----
$null = $results.Add( (Test-Step -Name "Audio STT: POST /audio/transcriptions" -Script {
  $h = @{ Authorization = "Bearer $KEY" }
  $r = Invoke-RestMethod -Method POST -Uri "$BASE/audio/transcriptions" -Headers $h -Form @{
    file = Get-Item $TtsPath
    model = "whisper-1"
    response_format = "json"
  }
  if (-not $r.text) { throw "No text field in transcription." }
}) )

# ---- 8) Files lifecycle ----
$null = $results.Add( (Test-Step -Name "Files: upload→list→download→delete" -Script {
  $h = @{ Authorization = "Bearer $KEY" }
  $up = Invoke-RestMethod -Method POST -Uri "$BASE/files" -Headers $h -Form @{
    file = Get-Item $TxtPath
    purpose = "assistants"
  }
  $fid = $up.id; if (-not $fid) { throw "Upload failed." }
  $ls = Invoke-Json -Path "/files"
  if (-not ($ls.data | Where-Object id -eq $fid)) { throw "Uploaded id not in list." }
  $dlPath = Join-Path $WorkDir "download.txt"
  Invoke-WebRequest -Uri "$BASE/files/$fid/content" -Headers $h -OutFile $dlPath | Out-Null
  if (-not (Test-Path $dlPath)) { throw "Download missing." }
  $del = Invoke-Json -Method DELETE -Path "/files/$fid"
  if (-not $del.deleted) { throw "Delete failed." }
}) )

# ---- 9) Assistants v2: list ----
$null = $results.Add( (Test-Step -Name "Assistants v2: GET /assistants" -Script {
  $uri = "$BASE/assistants"
  (Invoke-WebRequest -Method GET -Uri $uri -Headers $BetaHeaders).StatusCode | Out-Null
}) )

# ---- 10) Vector Stores: list ----
$null = $results.Add( (Test-Step -Name "Vector Stores: GET /vector_stores" -Script {
  $uri = "$BASE/vector_stores"
  (Invoke-WebRequest -Method GET -Uri $uri -Headers $BetaHeaders).StatusCode | Out-Null
}) )

# ---- 11) Realtime: WS round-trip ----
$null = $results.Add( (Test-Step -Name "Realtime: WS round-trip" -Script {
  Add-Type -AssemblyName System.Net.WebSockets
  $ws = [System.Net.WebSockets.ClientWebSocket]::new()
  $uri = [Uri]"$($BASE -replace '^http','ws')/realtime?model=gpt-4o-realtime-preview"
  $ws.Options.SetRequestHeader("Authorization","Bearer $KEY")
  $ws.ConnectAsync($uri,[Threading.CancellationToken]::None).Wait()

  $send = '{"type":"response.create","response":{"instructions":"say pong"}}'
  $bytes = [Text.Encoding]::UTF8.GetBytes($send)
  $seg = [ArraySegment[byte]]::new($bytes,0,$bytes.Length)
  $ws.SendAsync($seg,[System.Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None).Wait()

  $buf = New-Object byte[] 8192
  $seg = [ArraySegment[byte]]::new($buf)
  $cts = New-Object Threading.CancellationTokenSource(10000) # 10s
  $r = $ws.ReceiveAsync($seg,$cts.Token).Result
  $msg = [Text.Encoding]::UTF8.GetString($buf,0,$r.Count)
  $ws.Dispose()
  if (-not $msg -or $msg.Length -lt 5) { throw "No WS payload." }
}) )

# ---- Summary table ----
$fail = $results | Where-Object Status -eq "❌"
$ok   = $results | Where-Object Status -eq "✅"

$md = @()
$md += "# Relay Smoke Results"
$md += ""
$md += "| Check | Status | Notes |"
$md += "|---|:---:|---|"
foreach ($r in $results) {
  $notes = ($r.Notes ?? "") -replace '\|','\|' -replace "`n",' ' -replace "`r",' '
  $md += "| $($r.Name) | $($r.Status) | $notes |"
}
$md += ""
$md += "**Passed:** $($ok.Count)  **Failed:** $($fail.Count)"

$summary = $env:GITHUB_STEP_SUMMARY
if ($summary) { $md -join "`n" | Out-File -FilePath $summary -Encoding UTF8 }
$md -join "`n" | Write-Host

if ($fail.Count -gt 0) { exit 1 } else { exit 0 }
