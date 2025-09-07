
param(
  [string]$Base = "https://chatgpt-team.pages.dev",
  [int]$TimeoutSec = 120
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$summary = @()

function Add-Result([string]$name, [bool]$ok, [string]$detail="") {
  $global:summary += [pscustomobject]@{
    Test   = $name
    Result = $(if ($ok) { "PASS" } else { "FAIL" })
    Detail = $detail
  }
  if ($ok) { Write-Host "[PASS] $name" -ForegroundColor Green }
  else     { Write-Host "[FAIL] $name - $detail" -ForegroundColor Red }
}

function Post-Json([string]$uri, $obj, $headers=$null) {
  $json = $obj | ConvertTo-Json -Depth 12 -Compress
  return Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $json -Headers $headers -TimeoutSec 120
}

function Get-Json([string]$uri, $headers=$null) {
  return Invoke-RestMethod -Uri $uri -Method Get -Headers $headers -TimeoutSec 60
}

$IsPS7 = ($PSVersionTable.PSVersion.Major -ge 7)

# Optional: allow client Authorization via env var for local tests
$Headers = @{}
$CurlAuthArgs = @()
if ($env:OPENAI_CLIENT_KEY -and $env:OPENAI_CLIENT_KEY.Trim().Length -gt 0) {
  $Headers["Authorization"] = "Bearer " + $env:OPENAI_CLIENT_KEY
  $CurlAuthArgs += @("-H", "Authorization: Bearer " + $env:OPENAI_CLIENT_KEY)
}

function Curl-Json([string[]]$Args) {
  $out = & curl.exe @Args
  try { return $out | ConvertFrom-Json } catch { return $out }
}

# 1) Models
try {
  $models = Get-Json "$Base/v1/models" $Headers
  $ok = ($models -and $models.data -and $models.data.Count -gt 0)
  Add-Result "Models" $ok ("Returned " + ($models.data.Count) + " models")
} catch { Add-Result "Models" $false $_.Exception.Message }

# 2) Chat Completions
try {
  $body = @{ model="o4-mini"; messages=@(@{role="user";content="ping"}) }
  $chat = Post-Json "$Base/v1/chat/completions" $body $Headers
  $text = $chat.choices[0].message.content
  $ok = -not [string]::IsNullOrWhiteSpace($text)
  Add-Result "Chat Completions" $ok $text
} catch { Add-Result "Chat Completions" $false $_.Exception.Message }

# 3) Embeddings
try {
  $body = @{ model="text-embedding-3-small"; input="hello" }
  $emb = Post-Json "$Base/v1/embeddings" $body $Headers
  $ok = ($emb.data[0].embedding.Count -gt 0)
  Add-Result "Embeddings" $ok ("Dim=" + $emb.data[0].embedding.Count)
} catch { Add-Result "Embeddings" $false $_.Exception.Message }

# 4) Files: fine-tune JSONL upload -> download -> delete
try {
  $jsonlPath = Join-Path $env:TEMP ("relay-smoke-" + (Get-Random) + ".jsonl")
  $content = @'
{"messages":[{"role":"system","content":"You are concise."},{"role":"user","content":"ping?"},{"role":"assistant","content":"pong."}]}
{"messages":[{"role":"system","content":"You are concise."},{"role":"user","content":"what's 2+2?"},{"role":"assistant","content":"4."}]}
'@.Trim()
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($jsonlPath, $content, $utf8NoBom)

  if ($IsPS7 -and (Get-Command Invoke-RestMethod).Parameters.ContainsKey('Form')) {
    $up = Invoke-RestMethod -Uri "$Base/v1/files" -Method Post -Form @{
      file    = Get-Item $jsonlPath
      purpose = "fine-tune"
    } -Headers $Headers
  } else {
    $uploadArgs = @("-sS","-f","-X","POST","$Base/v1/files") + $CurlAuthArgs + @("-F",("file=@{0};type=application/jsonl" -f $jsonlPath),"-F","purpose=fine-tune")
    $up = Curl-Json $uploadArgs
  }

  if (-not $up.id) { throw ("Upload failed: " + ($up | Out-String)) }
  $fid = $up.id

  $dlPath = Join-Path $env:TEMP ("relay-smoke-dl-" + (Get-Random) + ".jsonl")
  if ($IsPS7 -and (Get-Command Invoke-WebRequest).Parameters.ContainsKey('OutFile')) {
    Invoke-WebRequest -Uri "$Base/v1/files/$fid/content" -OutFile $dlPath -Headers $Headers | Out-Null
  } else {
    $dlArgs = @("-sS","-f","-L","$Base/v1/files/$fid/content") + $CurlAuthArgs + @("-o",$dlPath)
    & curl.exe @dlArgs | Out-Null
  }

  $ok = (Test-Path $dlPath) -and ((Get-Item $dlPath).Length -gt 0)
  Add-Result "Files (upload+download)" $ok ("id=" + $fid)

  # cleanup
  Invoke-RestMethod -Uri "$Base/v1/files/$fid" -Method Delete -Headers $Headers | Out-Null
  Remove-Item -Force $jsonlPath,$dlPath -ErrorAction SilentlyContinue
} catch { Add-Result "Files (upload+download)" $false $_.Exception.Message }

# 5) Audio TTS
$mp3 = Join-Path $env:TEMP ("relay-tts-" + (Get-Random) + ".mp3")
try {
  $ttsBody = @{ model="gpt-4o-mini-tts"; voice="alloy"; input="Hello from the Cloudflare relay." } | ConvertTo-Json -Depth 6 -Compress
  Invoke-WebRequest -Uri "$Base/v1/audio/speech" -Method Post -ContentType "application/json" -Body $ttsBody -OutFile $mp3 -Headers $Headers | Out-Null
  $ok = (Test-Path $mp3) -and ((Get-Item $mp3).Length -gt 0)
  Add-Result "Audio TTS" $ok ("bytes=" + ((Get-Item $mp3).Length))
} catch { Add-Result "Audio TTS" $false $_.Exception.Message }

# 6) Audio STT (transcribe the MP3 back)
try {
  if ($IsPS7 -and (Get-Command Invoke-RestMethod).Parameters.ContainsKey('Form')) {
    $stt = Invoke-RestMethod -Uri "$Base/v1/audio/transcriptions" -Method Post -Form @{
      file  = Get-Item $mp3
      model = "gpt-4o-transcribe"
    } -Headers $Headers
  } else {
    $sttArgs = @("-sS","-f","-X","POST","$Base/v1/audio/transcriptions") + $CurlAuthArgs + @("-F",("file=@{0};type=audio/mpeg" -f $mp3),"-F","model=gpt-4o-transcribe")
    $stt = Curl-Json $sttArgs
  }

  $txt = $stt.text
  $ok = -not [string]::IsNullOrWhiteSpace($txt)
  Add-Result "Audio STT" $ok $txt
} catch { Add-Result "Audio STT" $false $_.Exception.Message }

# 7) Images (gpt-image-1)
$png = Join-Path $env:TEMP ("relay-img-" + (Get-Random) + ".png")
try {
  $imgReq = @{ model="gpt-image-1"; prompt="a glossy red sport motorcycle on a white studio background, 3/4 front view" }
  $imgRes = Post-Json "$Base/v1/images/generations" $imgReq $Headers
  $b64 = $imgRes.data[0].b64_json
  [IO.File]::WriteAllBytes($png, [Convert]::FromBase64String($b64))
  $ok = (Test-Path $png) -and ((Get-Item $png).Length -gt 0)
  Add-Result "Images (generation)" $ok ("bytes=" + ((Get-Item $png).Length))
} catch { Add-Result "Images (generation)" $false $_.Exception.Message }

# 8) Assistants v2 minimal
try {
  $asst = Post-Json "$Base/v1/assistants" @{ model="gpt-4o-mini"; name="Relay Smoke Assistant"; instructions="Answer briefly." } $Headers
  $aid = $asst.id

  $thr  = Invoke-RestMethod "$Base/v1/threads" -Method Post -Headers $Headers
  $tid  = $thr.id
  Invoke-RestMethod "$Base/v1/threads/$tid/messages" -Method Post -ContentType "application/json" -Headers $Headers `
    -Body (@{ role="user"; content="Say 'ok'." } | ConvertTo-Json -Depth 6 -Compress) | Out-Null

  $run = Post-Json "$Base/v1/threads/$tid/runs" @{ assistant_id=$aid } $Headers
  $rid = $run.id

  $elapsed = 0
  do {
    Start-Sleep -Seconds 2
    $elapsed += 2
    $run = Get-Json "$Base/v1/threads/$tid/runs/$rid" $Headers
  } while ($elapsed -lt $TimeoutSec -and ($run.status -in @("queued","in_progress")))

  if ($run.status -ne "completed") { throw "Run status $($run.status)" }

  $msgs = Get-Json "$Base/v1/threads/$tid/messages?limit=5" $Headers
  $reply = ($msgs.data | Where-Object { $_.role -eq "assistant" } | Select-Object -First 1).content[0].text.value
  $ok = -not [string]::IsNullOrWhiteSpace($reply)
  Add-Result "Assistants v2" $ok $reply
} catch { Add-Result "Assistants v2" $false $_.Exception.Message }

# Summary
Write-Host ""
Write-Host "==== Relay Smoke Summary ===="
$summary | Format-Table -AutoSize | Out-String | Write-Host

$fail = ($summary | Where-Object { $_.Result -eq "FAIL" }).Count
$pass = ($summary | Where-Object { $_.Result -eq "PASS" }).Count
Write-Host ("PASS: {0}  FAIL: {1}" -f $pass, $fail)

if ($fail -gt 0) { exit 1 } else { exit 0 }
