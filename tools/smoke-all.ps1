param(
  [string]$Base = "https://chatgpt-team.pages.dev/v1",
  [string]$WS   = "wss://chatgpt-team-realtime.virelai.workers.dev/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
  [string]$Log  = "C:\Users\User\Desktop\run result.txt"
)
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $Log) { Remove-Item -LiteralPath $Log -Force }
function Log([string]$m){ $ts=(Get-Date).ToString("s"); "$ts $m" | Out-File -LiteralPath $Log -Append -Encoding utf8 }
if(-not $env:OPENAI_API_KEY){ $env:OPENAI_API_KEY = Read-Host "OpenAI API key (session only)" }
$H=@{ Authorization="Bearer $($env:OPENAI_API_KEY)"; 'Content-Type'='application/json' }

Log "START: smoke-all (HTTPS)"

# Health
try { $hp=Invoke-RestMethod "$Base/health" -TimeoutSec 20; Log ("HEALTH relay: " + ($hp|ConvertTo-Json -Depth 10 -Compress)) } catch { Log "HEALTH relay ERR: $($_.Exception.Message)" }
try { $hrt=Invoke-RestMethod ("{0}/health-rt" -f ($WS -replace '/realtime\?.*$','')); Log ("HEALTH-RT: " + ($hrt|ConvertTo-Json -Depth 10 -Compress)) } catch { Log "HEALTH-RT ERR: $($_.Exception.Message)" }

# Helper
function Test-HTTP3x([string]$uri,[string]$bodyJson=''){
  $ok=$true
  try { Invoke-RestMethod -Uri $uri -Method POST -Headers $H -Body $bodyJson -TimeoutSec 60 | Out-Null; Log "IRM OK: $uri" } catch { Log "IRM ERR: $uri :: $($_.Exception.Message)"; $ok=$false }
  try { $w=Invoke-WebRequest -UseBasicParsing -Uri $uri -Method POST -Headers $H -Body $bodyJson -TimeoutSec 60; Log "IWR OK: $uri :: $($w.StatusCode)" } catch { Log "IWR ERR: $uri :: $($_.Exception.Message)"; $ok=$false }
  try { $tmp=New-TemporaryFile; Set-Content -LiteralPath $tmp -Value $bodyJson -Encoding utf8; & curl.exe -sS -X POST -H "Authorization: $($H.Authorization)" -H "Content-Type: application/json" --data "@$tmp" $uri | Out-Null; Log "CURL OK: $uri"; Remove-Item -LiteralPath $tmp -Force } catch { Log "CURL ERR: $uri :: $($_.Exception.Message)"; $ok=$false }
  return $ok
}

# Models
try { Invoke-RestMethod "$Base/models" -Headers $H -TimeoutSec 30 | Out-Null; Log "MODELS OK" } catch { Log "MODELS ERR: $($_.Exception.Message)" }

# Chat
$chat = @{ model="gpt-4o-mini"; messages=@(@{role="user"; content="Say 'pong' only."}); max_tokens=8 } | ConvertTo-Json -Depth 6
[void](Test-HTTP3x "$Base/chat/completions" $chat)

# Responses (+SSE)
$resp = @{ model="gpt-5-mini"; input="Say hi in one word."; max_output_tokens=16 } | ConvertTo-Json -Depth 6
[void](Test-HTTP3x "$Base/responses" $resp)
try { & curl.exe -sN -H "Authorization: $($H.Authorization)" -H "Content-Type: application/json" -H "Accept: text/event-stream" -d $resp "$Base/responses" | Select-Object -First 3 | Out-Null; Log "RESPONSES SSE OK" } catch { Log "RESPONSES SSE ERR: $($_.Exception.Message)" }

# Embeddings
$emb = @{ model="text-embedding-3-small"; input="hello world" } | ConvertTo-Json -Depth 6
[void](Test-HTTP3x "$Base/embeddings" $emb)

# Images
$img = @{ model="gpt-image-1"; prompt="a minimalist red koi logo" } | ConvertTo-Json -Depth 6
[void](Test-HTTP3x "$Base/images/generations" $img)

# ----- Audio: TTS -----
try {
  $ttsBody = @{ model="gpt-4o-mini-tts"; input="This is a relay TTS test"; voice="alloy"; format="wav" } | ConvertTo-Json -Depth 6
  $ttsBytes = Invoke-RestMethod "$Base/audio/speech" -Method POST -Headers $H -Body $ttsBody -TimeoutSec 120
  if ($ttsBytes) { Log "AUDIO TTS OK (non-empty)" } else { Log "AUDIO TTS WARN (empty body)" }
} catch { Log "AUDIO TTS ERR: $($_.Exception.Message)" }

# ----- Audio: STT + Translations (valid WAV + correct multipart) -----
try {
  # build 1s of silence WAV (PCM16 mono 16k)
  $wav = Join-Path $env:TEMP "silence-16k-mono-1s.wav"
  $dataLen = 16000 * 2
  $fs=[IO.File]::Create($wav); $bw=[IO.BinaryWriter]::new($fs)
  function W16($v){ $bw.Write([UInt16]$v) }
  $bw.Write([Text.Encoding]::ASCII.GetBytes("RIFF")); $bw.Write([UInt32](36+$dataLen))
  $bw.Write([Text.Encoding]::ASCII.GetBytes("WAVEfmt ")); $bw.Write([UInt32]16); W16 1; W16 1
  $bw.Write([UInt32]16000); $bw.Write([UInt32]32000); W16 2; W16 16
  $bw.Write([Text.Encoding]::ASCII.GetBytes("data")); $bw.Write([UInt32]$dataLen)
  $bw.Write((,0 * $dataLen)); $bw.Flush(); $bw.Close(); $fs.Close()

  $client = [System.Net.Http.HttpClient]::new()
  $client.DefaultRequestHeaders.Add("Authorization",$H.Authorization)

  # /audio/transcriptions
  $form1 = [System.Net.Http.MultipartFormDataContent]::new()
  $file1 = New-Object System.Net.Http.ByteArrayContent( ,([IO.File]::ReadAllBytes($wav)) )
  $file1.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("audio/wav")
  $form1.Add($file1,"file","silence.wav")
  $form1.Add([System.Net.Http.StringContent]::new('whisper-1'),"model")
  $r1 = $client.PostAsync("$Base/audio/transcriptions",$form1).GetAwaiter().GetResult()
  if ($r1.IsSuccessStatusCode){ Log "AUDIO STT OK" } else { Log ("AUDIO STT ERR: {0}" -f $r1.StatusCode) }

  # /audio/translations
  $form2 = [System.Net.Http.MultipartFormDataContent]::new()
  $file2 = New-Object System.Net.Http.ByteArrayContent( ,([IO.File]::ReadAllBytes($wav)) )
  $file2.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("audio/wav")
  $form2.Add($file2,"file","silence.wav")
  $form2.Add([System.Net.Http.StringContent]::new('whisper-1'),"model")
  $r2 = $client.PostAsync("$Base/audio/translations",$form2).GetAwaiter().GetResult()
  if ($r2.IsSuccessStatusCode){ Log "AUDIO TRN OK" } else { Log ("AUDIO TRN ERR: {0}" -f $r2.StatusCode) }
} catch { Log "AUDIO STT/TRN ERR: $($_.Exception.Message)" }

# Files list
try { $files = Invoke-RestMethod "$Base/files" -Headers $H -TimeoutSec 60; Log ("FILES LIST OK count=" + ($files.data.Count)) } catch { Log "FILES LIST ERR: $($_.Exception.Message)" }

# Background via /background (shim) -> poll + SSE
try {
  $b = @{ model="gpt-5-mini"; input="background: return 'ok'"; task_type="response.create" } | ConvertTo-Json -Depth 6
  $created = Invoke-RestMethod "$Base/background" -Method POST -Headers $H -Body $b -TimeoutSec 60
  $id = $created.id
  if ($id){ Log ("BACKGROUND OK id=" + $id); Start-Sleep 2; $st = Invoke-RestMethod "$Base/responses/$id" -Headers $H -TimeoutSec 30; Log ("BACKGROUND STATUS: id=$id status=" + $st.status); & curl.exe -sN -H "Authorization: $($H.Authorization)" -H "Accept: text/event-stream" "$Base/responses/$id?stream=true" | Select-Object -First 3 | Out-Null; Log ("BACKGROUND RESUME SSE OK id=" + $id) } else { Log "BACKGROUND WARN: missing id" }
} catch { Log "BACKGROUND ERR: $($_.Exception.Message)" }

# Moderations
try { $m=@{ model="omni-moderation-latest"; input="test" }|ConvertTo-Json -Depth 6; Invoke-RestMethod "$Base/moderations" -Method POST -Headers $H -Body $m -TimeoutSec 20 | Out-Null; Log "MODERATIONS WARN: expected blocked but got success" } catch { Log "MODERATIONS BLOCKED (expected)" }

# Realtime WS (101 only)
Add-Type -AssemblyName System.Net.WebSockets
function Test-WS101([string]$Uri,[string]$Proto,[int]$TimeoutSec=3){
  $sw=[Diagnostics.Stopwatch]::StartNew()
  $ws=[System.Net.WebSockets.ClientWebSocket]::new()
  if ($Proto){ $ws.Options.AddSubProtocol($Proto) }
  $ws.Options.SetRequestHeader("OpenAI-Beta","realtime=v1")
  $cts=[Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds($TimeoutSec))
  try {
    $ws.ConnectAsync([Uri]$Uri,$cts.Token).GetAwaiter().GetResult()
    $sw.Stop()
    if ($ws.State -eq [System.Net.WebSockets.WebSocketState]::Open) { Log ("WS PASS {0} in {1:n1}s" -f $Proto,$sw.Elapsed.TotalSeconds); $true } else { Log ("WS FAIL {0} state={1}" -f $Proto,$ws.State); $false }
  } catch { $sw.Stop(); Log ("WS ERR {0}: {1} ({2:n1}s)" -f $Proto,$_.Exception.Message,$sw.Elapsed.TotalSeconds); $false }
  finally { try { $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure,"probe",[Threading.CancellationToken]::None).GetAwaiter().GetResult() } catch {}; $ws.Dispose(); $cts.Dispose() }
}
$ok1=Test-WS101 -Uri $WS -Proto "oai-realtime"
$ok2=Test-WS101 -Uri $WS -Proto "oai-realtime-broker"
if($ok1 -and $ok2){ Log "WS 101 OK (two subprotocols)" } else { Log "WS 101 NOT OK" }

Log "END: smoke-all complete"
