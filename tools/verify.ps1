param(
  [string]$Base = "https://chatgpt-team.pages.dev",
  [string]$WS   = "wss://chatgpt-team-realtime.virelai.workers.dev",
  [string]$Key  = $env:OPENAI_API_KEY,
  [switch]$DeepAssistants,      # toggles create/run instead of list-only
  [string]$SampleAudio = "",    # optional WAV/MP3 path for STT test
  [string]$SampleFile  = ""     # optional file path for Files API test
)

# ---------- helpers ----------
function Write-Step($name,$ok){ $s= if($ok){"OK"}else{"FAIL"}; "{0,-24} {1}" -f $name,$s }
function Get-Json($s){ if([string]::IsNullOrWhiteSpace($s)){return $null}; try{ $s|ConvertFrom-Json -Depth 20 }catch{ $null } }

$ErrorActionPreference="Stop"
$Key = ($Key ?? "").Trim()

if (-not $Key) { Write-Host (Write-Step "ENV KEY" $false); throw "OPENAI_API_KEY missing"; } else { Write-Host (Write-Step "ENV KEY" $true) }

# shared headers
$H = @{
  "Authorization" = "Bearer $Key"
  "Content-Type"  = "application/json"
}

# ---------- 0. basic env/auth ----------
try { gh auth status | Out-Null; Write-Host (Write-Step "GitHub CLI" $true) } catch { Write-Host (Write-Step "GitHub CLI" $false) }
try { npx wrangler whoami | Out-Null; Write-Host (Write-Step "Wrangler Login" $true) } catch { Write-Host (Write-Step "Wrangler Login" $false) }

# ---------- 1. health ----------
try {
  $h1 = Invoke-RestMethod "$Base/health"
  $h2 = Invoke-RestMethod "$Base/v1/health"
  $ok = $h1.ok -and $h2.ok
  Write-Host (Write-Step "Health (/health)" $ok)
  Write-Host (Write-Step "Health (/v1/health)" $ok)
} catch { Write-Host (Write-Step "Health" $false) }

# ---------- 2. models ----------
try {
  $m = Invoke-RestMethod -Method GET -Headers $H -Uri "$Base/v1/models"
  Write-Host (Write-Step "GET /v1/models" ($null -ne $m.data))
} catch { Write-Host (Write-Step "GET /v1/models" $false) }

# ---------- 3. chat completions ----------
try {
  $body = @{ model="gpt-4o-mini"; messages=@(@{role="user"; content="Say 'pong'."}); max_tokens=8 } | ConvertTo-Json -Depth 5
  $c = Invoke-RestMethod -Method POST -Headers $H -Body $body -Uri "$Base/v1/chat/completions"
  $txt = $c.choices[0].message.content
  Write-Host (Write-Step "POST /v1/chat/completions" ([string]::IsNullOrWhiteSpace($txt) -eq $false))
} catch { Write-Host (Write-Step "POST /v1/chat/completions" $false) }

# ---------- 4. embeddings ----------
try {
  $emb = @{ model="text-embedding-3-small"; input="hello world" } | ConvertTo-Json
  $e = Invoke-RestMethod -Method POST -Headers $H -Body $emb -Uri "$Base/v1/embeddings"
  $len = $e.data[0].embedding.Count
  Write-Host (Write-Step "POST /v1/embeddings" ($len -gt 0))
} catch { Write-Host (Write-Step "POST /v1/embeddings" $false) }

# ---------- 5. files (optional if path given) ----------
if ($SampleFile -and (Test-Path $SampleFile)) {
  try {
    $upl = Invoke-WebRequest -Method POST -Headers @{ Authorization="Bearer $Key" } -Uri "$Base/v1/files" -Form @{
      file = Get-Item $SampleFile
      purpose = "assistants"
    }
    $jid = (Get-Json $upl.Content).id
    $lst = Invoke-RestMethod -Method GET -Headers $H -Uri "$Base/v1/files"
    $has = $false
    foreach($f in $lst.data){ if($f.id -eq $jid){ $has=$true; break } }
    Write-Host (Write-Step "Files upload/list" ($has -and $jid))
    if ($jid) {
      # delete
      $del = Invoke-RestMethod -Method DELETE -Headers $H -Uri "$Base/v1/files/$jid"
      Write-Host (Write-Step "Files delete" ($del.deleted -eq $true))
    }
  } catch { Write-Host (Write-Step "Files API" $false) }
} else {
  Write-Host (Write-Step "Files API (skipped)" $true)
}

# ---------- 6. audio (optional if path given) ----------
if ($SampleAudio -and (Test-Path $SampleAudio)) {
  try {
    # STT transcription
    $client = [System.Net.Http.HttpClient]::new()
    $client.DefaultRequestHeaders.Authorization = "Bearer $Key"
    $mp = [System.Net.Http.MultipartFormDataContent]::new()
    $ba = [System.IO.File]::ReadAllBytes($SampleAudio)
    $bc = [System.Net.Http.ByteArrayContent]::new($ba)
    $bc.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("audio/wav")
    $mp.Add($bc,"file",[IO.Path]::GetFileName($SampleAudio))
    $mp.Add([System.Net.Http.StringContent]::new("whisper-1"),"model")
    $resp = $client.PostAsync("$Base/v1/audio/transcriptions",$mp).Result
    $ok = $resp.IsSuccessStatusCode
    Write-Host (Write-Step "Audio STT" $ok)
  } catch { Write-Host (Write-Step "Audio STT" $false) }
} else {
  Write-Host (Write-Step "Audio STT (skipped)" $true)
}

# ---------- 7. assistants v2 (safe mode by default) ----------
try {
  $alist = Invoke-RestMethod -Method GET -Headers ($H + @{"OpenAI-Beta"="assistants=v2"}) -Uri "$Base/v1/assistants"
  $safeOk = $null -ne $alist.data
  if (-not $DeepAssistants) {
    Write-Host (Write-Step "Assistants v2 (list)" $safeOk)
  } else {
    $aBody = @{ name="temp-mini"; model="gpt-4o-mini"; instructions="You say pong once." } | ConvertTo-Json
    $a = Invoke-RestMethod -Method POST -Headers ($H + @{"OpenAI-Beta"="assistants=v2"}) -Body $aBody -Uri "$Base/v1/assistants"
    $aid = $a.id
    $t = Invoke-RestMethod -Method POST -Headers ($H + @{"OpenAI-Beta"="assistants=v2"}) -Body (@{messages=@(@{role="user";content="ping"})}|ConvertTo-Json) -Uri "$Base/v1/threads"
    $tid = $t.id
    $r  = Invoke-RestMethod -Method POST -Headers ($H + @{"OpenAI-Beta"="assistants=v2"}) -Body (@{assistant_id=$aid}|ConvertTo-Json) -Uri "$Base/v1/threads/$tid/runs"
    $ok = $aid -and $tid -and $r.id
    Write-Host (Write-Step "Assistants v2 (create/run)" $ok)
    if($aid){ Invoke-RestMethod -Method DELETE -Headers ($H + @{"OpenAI-Beta"="assistants=v2"}) -Uri "$Base/v1/assistants/$aid" | Out-Null }
  }
} catch { Write-Host (Write-Step "Assistants v2" $false) }

# ---------- 8. realtime handshake (101) ----------
try {
  $rt = "$($Base.Replace('https://','https://').TrimEnd('/'))/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
  # Use the worker host if provided (preferred)
  if ($WS) { $rt = "$($WS.TrimEnd('/'))/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17" -replace '^wss://','https://' }
  $key16 = [Convert]::ToBase64String((1..16 | % {Get-Random -Max 256}))
  $cmd = "curl.exe --http1.1 -m 2 --connect-timeout 1 -s -o NUL -w %{http_code} -H `"Connection: Upgrade`" -H `"Upgrade: websocket`" -H `"Sec-WebSocket-Version: 13`" -H `"Sec-WebSocket-Key: $key16`" -H `"Authorization: Bearer $Key`" `"$rt`""
  $code = cmd /c $cmd
  Write-Host (Write-Step "Realtime WS 101" ($code -eq "101"))
} catch { Write-Host (Write-Step "Realtime WS 101" $false) }

# ---------- 9. realtime round-trip ----------
try {
  Add-Type -AssemblyName System.Net.WebSockets
  $uri = if ($WS) { "$WS/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17" } else { "$Base/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17" -replace '^https','wss' }
  $ws = [System.Net.WebSockets.ClientWebSocket]::new()
  $ws.Options.SetRequestHeader("Authorization","Bearer $Key")
  $ct=[Threading.CancellationToken]::None
  $ws.ConnectAsync([Uri]$uri,$ct).GetAwaiter().GetResult()
  $msg = '{ "type": "response.create", "response": { "instructions": "Say pong once." } }'
  $buf = [System.Text.Encoding]::UTF8.GetBytes($msg)
  $seg = [ArraySegment[byte]]::new($buf,0,$buf.Length)
  $ws.SendAsync($seg,[System.Net.WebSockets.WebSocketMessageType]::Text,$true,$ct).GetAwaiter().GetResult()
  $rbuf = New-Object byte[] 4096
  $r = $ws.ReceiveAsync([ArraySegment[byte]]::new($rbuf,0,$rbuf.Length),$ct).GetAwaiter().GetResult()
  $txt = [System.Text.Encoding]::UTF8.GetString($rbuf,0,$r.Count)
  $ok = $txt.Length -gt 0
  $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure,"ok",$ct).GetAwaiter().GetResult()
  Write-Host (Write-Step "Realtime round-trip" $ok)
} catch { Write-Host (Write-Step "Realtime round-trip" $false) }

Write-Host "`nDone."
