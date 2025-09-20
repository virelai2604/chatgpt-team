param(
  [string]$Base = "https://chatgpt-team.pages.dev/v1",
  [string]$WS   = "wss://chatgpt-team-realtime.virelai.workers.dev/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
  [int]$Timeout = 45
)
$ErrorActionPreference='Stop'
if(-not $env:OPENAI_API_KEY){ $env:OPENAI_API_KEY = Read-Host "OpenAI API key (session only)" }
$H = @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; 'Content-Type'='application/json' }

function L([string]$s){ $ts=(Get-Date).ToString('s'); "$ts $s" }

# -- 0) health --
try { $hp=Invoke-RestMethod "$($Base.TrimEnd('/'))/health" -TimeoutSec 15; L("HEALTH relay: "+($hp|ConvertTo-Json -Compress)) | Write-Output } catch { L("HEALTH relay ERR: $($_.Exception.Message)") | Write-Output }

# -- 1) models --
try { Invoke-RestMethod "$Base/models" -Headers $H -TimeoutSec 20 | Out-Null; L("MODELS OK") | Write-Output } catch { L("MODELS ERR: $($_.Exception.Message)") | Write-Output }

# helper to try irm/iwr/curl
function Hit3([string]$uri,[string]$json){ 
  $ok=$true
  try{ Invoke-RestMethod -Uri $uri -Method POST -Headers $H -Body $json -TimeoutSec $Timeout | Out-Null; L("IRM OK: $uri") | Write-Output } catch { L("IRM ERR: $uri :: $($_.Exception.Message)") | Write-Output; $ok=$false }
  try{ $w=Invoke-WebRequest -UseBasicParsing -Uri $uri -Method POST -Headers $H -Body $json -TimeoutSec $Timeout; L("IWR OK: $uri :: $($w.StatusCode)") | Write-Output } catch { L("IWR ERR: $uri :: $($_.Exception.Message)") | Write-Output; $ok=$false }
  try{ $tmp=New-TemporaryFile; Set-Content -LiteralPath $tmp -Value $json -Encoding utf8; & curl.exe -sS -X POST -H "Authorization: $($H.Authorization)" -H "Content-Type: application/json" --data "@$tmp" $uri | Out-Null; L("CURL OK: $uri") | Write-Output; Remove-Item -LiteralPath $tmp -Force } catch { L("CURL ERR: $uri :: $($_.Exception.Message)") | Write-Output; $ok=$false }
  return $ok
}

# -- 2) chat/completions (legacy) --
$chat = @{ model="gpt-4o-mini"; messages=@(@{role="user"; content="Say pong."}); max_tokens=8 } | ConvertTo-Json -Depth 6
[void](Hit3 "$Base/chat/completions" $chat)

# -- 3) responses + SSE --
$resp = @{ model="gpt-5-mini"; input="hi"; max_output_tokens=16 } | ConvertTo-Json -Depth 6
[void](Hit3 "$Base/responses" $resp)
try{ & curl.exe -sN -H "Authorization: $($H.Authorization)" -H "Content-Type: application/json" -H "Accept: text/event-stream" -d $resp "$Base/responses" | Select-Object -First 3 | Out-Null; L("RESPONSES SSE OK") | Write-Output } catch { L("RESPONSES SSE ERR: $($_.Exception.Message)") | Write-Output }

# -- 4) embeddings --
$emb = @{ model="text-embedding-3-small"; input="hello world" } | ConvertTo-Json
[void](Hit3 "$Base/embeddings" $emb)

# -- 5) images/generations --
$img = @{ model="gpt-image-1"; prompt="a minimalist red koi logo" } | ConvertTo-Json
[void](Hit3 "$Base/images/generations" $img)

# -- 6) audio: TTS + STT + translations (multipart, no tricky -replace) --
try{
  # TTS (JSON → audio)
  $tts = @{ model="gpt-4o-mini-tts"; input="This is a test"; voice="alloy" } | ConvertTo-Json
  $bytes = Invoke-RestMethod "$Base/audio/speech" -Method POST -Headers $H -Body $tts -TimeoutSec 60
  if($bytes){ L("AUDIO TTS OK (non-empty)") | Write-Output } else { L("AUDIO TTS WARN (empty)") | Write-Output }
} catch { L("AUDIO TTS ERR: $($_.Exception.Message)") | Write-Output }

# Build a 1s 16k mono WAV (silence)
$wav = Join-Path $env:TEMP "silence-16k-mono-1s.wav"
[IO.File]::WriteAllBytes($wav, [byte[]](0..(16000*2-1) | ForEach-Object { 0 } ))

# Proper multipart upload for STT and TRN
try{
  $client = [System.Net.Http.HttpClient]::new()
  $client.Timeout = [TimeSpan]::FromSeconds(60)
  $client.DefaultRequestHeaders.Add("Authorization",$H.Authorization)

  $fn = "silence.wav"
  $b  = [IO.File]::ReadAllBytes($wav)

  foreach($path in @("transcriptions","translations")){
    $form = [System.Net.Http.MultipartFormDataContent]::new()
    $file = New-Object System.Net.Http.ByteArrayContent( ,$b )
    $file.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("audio/wav")
    $form.Add($file,"file",$fn)
    $form.Add([System.Net.Http.StringContent]::new("whisper-1"),"model")
    $u = "$Base/audio/$path"
    $r = $client.PostAsync($u,$form).GetAwaiter().GetResult()
    if($r.IsSuccessStatusCode){ L(("AUDIO {0} OK" -f ($path -eq "transcriptions" ? "STT" : "TRN"))) | Write-Output } else { L(("AUDIO {0} ERR: {1}" -f ($path -eq "transcriptions" ? "STT" : "TRN"), $r.StatusCode)) | Write-Output }
  }
} catch { L("AUDIO STT/TRN ERR: $($_.Exception.Message)") | Write-Output }

# -- 7) files list (sanity) --
try{ $f=Invoke-RestMethod "$Base/files" -Headers $H -TimeoutSec 30; L("FILES LIST OK count="+$f.data.Count) | Write-Output } catch { L("FILES LIST ERR: $($_.Exception.Message)") | Write-Output }

# -- 8) background (optional; preview-safe)
try{
  $bg = @{ model="gpt-5-mini"; input="ok"; background=$true } | ConvertTo-Json -Depth 6
  $res = Invoke-RestMethod "$Base/responses" -Method POST -Headers $H -Body $bg -TimeoutSec $Timeout
  if($res.background -and $res.id){ L("BG_CREATE OK: "+($res | ConvertTo-Json -Compress)) | Write-Output
    Start-Sleep -Seconds 2
    $poll = Invoke-RestMethod "$Base/responses/$($res.id)" -Headers $H -TimeoutSec 30
    L("BG_POLL: "+($poll | ConvertTo-Json -Compress)) | Write-Output
  } else { L("BACKGROUND SKIP (not supported)") | Write-Output }
} catch { L("BACKGROUND ERR: $($_.Exception.Message)") | Write-Output }

# -- 9) moderations must be blocked --
try{
  $m = @{ model="omni-moderation-latest"; input="test" } | ConvertTo-Json
  Invoke-RestMethod "$Base/moderations" -Method POST -Headers $H -Body $m -TimeoutSec 20 | Out-Null
  L("MODERATIONS WARN: expected blocked but got success") | Write-Output
} catch { L("MODERATIONS BLOCKED (expected)") | Write-Output }

# -- 10) realtime WS 101 (two subprotocols) --
Add-Type -AssemblyName System.Net.WebSockets
function Test-WS101([string]$Uri,[string]$Proto,[int]$TimeoutSec=2){
  $sw=[Diagnostics.Stopwatch]::StartNew()
  $ws=[System.Net.WebSockets.ClientWebSocket]::new()
  $ws.Options.AddSubProtocol($Proto)
  $ws.Options.SetRequestHeader("OpenAI-Beta","realtime=v1")
  $cts=[Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds($TimeoutSec))
  try{
    $ws.ConnectAsync([Uri]$Uri,$cts.Token).GetAwaiter().GetResult()
    $sw.Stop()
    if($ws.State -eq [System.Net.WebSockets.WebSocketState]::Open){ L(("WS PASS {0} in {1:n1}s" -f $Proto,$sw.Elapsed.TotalSeconds)) | Write-Output; $true } else { L(("WS FAIL {0} state={1}" -f $Proto,$ws.State)) | Write-Output; $false }
  } catch { $sw.Stop(); L(("WS ERR {0}: {1} ({2:n1}s)" -f $Proto,$_.Exception.Message,$sw.Elapsed.TotalSeconds)) | Write-Output; $false }
  finally { try{ $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure,"probe",[Threading.CancellationToken]::None).GetAwaiter().GetResult() } catch{}; $ws.Dispose(); $cts.Dispose() }
}
$w1=Test-WS101 -Uri $WS -Proto "oai-realtime" -TimeoutSec 2
$w2=Test-WS101 -Uri $WS -Proto "oai-realtime-broker" -TimeoutSec 2
if($w1 -and $w2){ L("WS 101 OK (two subprotocols)") | Write-Output } else { L("WS 101 NOT OK") | Write-Output }

L("END: smoke-all complete") | Write-Output
