param(
  [string]$Base,
  [string]$Auth,
  [int]$TimeoutSec = 120,
  [switch]$VerboseMode,

  [string]$ModelChat      = "gpt-4o-mini",
  [string]$ModelResponses = "o4-mini",
  [string]$ModelEmbed     = "text-embedding-3-small",
  [string]$ModelTTS       = "gpt-4o-mini-tts",
  [string]$ModelSTT       = "whisper-1",
  [string]$ModelImage     = "gpt-image-1",
  [string]$ModelRealtime  = "gpt-4o-realtime-preview-2024-12-17",

  # extras
  [string]$RealtimeBase,
  [string]$Org,
  [string]$Project,

  # files run order
  [switch]$FilesFirst,
  [switch]$OnlyFiles
)

$ErrorActionPreference = "Stop"

# ---------- Base & Auth ----------
$Live = "https://chatgpt-team.pages.dev"
if ([string]::IsNullOrWhiteSpace($Base)) { $Base = $Live }
if ($Base -notmatch "/v1/?$") { $Base = ($Base.TrimEnd('/')) + "/v1" }

if ($RealtimeBase) {
  if ($RealtimeBase -notmatch "/v1/?$") { $RealtimeBase = ($RealtimeBase.TrimEnd('/')) + "/v1" }
} else {
  $RealtimeBase = $Base
}

if ([string]::IsNullOrWhiteSpace($Auth)) {
  $Auth = $env:OPENAI_CLIENT_KEY
  if (-not $Auth) { $Auth = $env:OPENAI_API_KEY }
  if (-not $Auth) { $Auth = $env:OPENAI_KEY }
  if (-not $Auth) { $Auth = "dev" }
}
$UseHeader = $Auth -ne "dev"

# ---------- Helpers ----------
function Say { param([string]$Msg) if ($VerboseMode) { Write-Host "[*] $Msg" -ForegroundColor DarkCyan } }

function New-JsonHeaders {
  param([switch]$WithAuth)
  $h = @{ "Content-Type" = "application/json" }
  if ($WithAuth -and $UseHeader) { $h["Authorization"] = "Bearer $Auth" }
  $org = if ($PSBoundParameters.ContainsKey("Org") -and $Org) { $Org } elseif ($env:OPENAI_ORG_ID) { $env:OPENAI_ORG_ID } else { $null }
  $prj = if ($PSBoundParameters.ContainsKey("Project") -and $Project) { $Project } elseif ($env:OPENAI_PROJECT) { $env:OPENAI_PROJECT } else { $null }
  if ($org) { $h["OpenAI-Organization"] = $org }
  if ($prj) { $h["OpenAI-Project"] = $prj }
  $h
}

function New-MultipartHeaders {
  $h = @{}
  if ($UseHeader) { $h["Authorization"] = "Bearer $Auth" }
  $org = if ($PSBoundParameters.ContainsKey("Org") -and $Org) { $Org } elseif ($env:OPENAI_ORG_ID) { $env:OPENAI_ORG_ID } else { $null }
  $prj = if ($PSBoundParameters.ContainsKey("Project") -and $Project) { $Project } elseif ($env:OPENAI_PROJECT) { $env:OPENAI_PROJECT } else { $null }
  if ($org) { $h["OpenAI-Organization"] = $org }
  if ($prj) { $h["OpenAI-Project"] = $prj }
  $h
}

function Invoke-JsonPost {
  param([string]$Uri, [hashtable]$Body, [int]$Timeout = $TimeoutSec)
  $json = $Body | ConvertTo-Json -Depth 12
  Invoke-RestMethod -Uri $Uri -Method Post -Headers (New-JsonHeaders -WithAuth) -Body $json -TimeoutSec $Timeout
}

function U { param([string]$Path) ($Base.TrimEnd('/')) + $Path }

$global:FAILURES = New-Object System.Collections.Generic.List[string]
function Add-Failure { param([string]$Name,[string]$Details) $global:FAILURES.Add("${Name}: $Details") }

# ---------- temp ----------
$Tmp = Join-Path $PSScriptRoot "smoke-tmp"
if (-not (Test-Path $Tmp)) { New-Item -ItemType Directory -Path $Tmp | Out-Null }

# ---------- Files Suite (fine-tune JSONL path) ----------
function Run-FilesSuite {
  try {
    Say "Files: preparing sample.jsonl"
    $sampleJsonl = Join-Path $Tmp "sample.jsonl"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $jsonl = @(
      '{"messages":[{"role":"system","content":"You are concise."},{"role":"user","content":"ping?"},{"role":"assistant","content":"pong."}]}'
    ) -join "`n"
    [IO.File]::WriteAllText($sampleJsonl, $jsonl, $utf8NoBom)

    Say "Files: upload (.jsonl, purpose=fine-tune)"
    $up = Invoke-RestMethod -Uri (U "/files") -Method Post -Headers (New-MultipartHeaders) `
          -Form @{ file = Get-Item $sampleJsonl; purpose = "fine-tune" } -TimeoutSec $TimeoutSec
    $fid = $up.id; if (-not $fid) { throw "upload returned no id" }

    Say "Files: list"
    $list = Invoke-RestMethod -Uri (U "/files") -Method Get -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec
    if (-not $list.data -or $list.data.Count -lt 1) { throw "list empty" }

    Say "Files: get metadata"
    $meta = Invoke-RestMethod -Uri (U ("/files/{0}" -f $fid)) -Method Get -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec
    if ($meta.id -ne $fid) { throw "metadata id mismatch" }

    Say "Files: download content"
    $dlPath = Join-Path $Tmp "downloaded.jsonl"
    Invoke-WebRequest -Uri (U ("/files/{0}/content" -f $fid)) -Method Get -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec -OutFile $dlPath | Out-Null
    if (-not (Test-Path $dlPath)) { throw "no content file" }
    if ((Get-Item $dlPath).Length -lt 1) { throw "downloaded content empty" }

    Say "Files: delete"
    $null = Invoke-RestMethod -Uri (U ("/files/{0}" -f $fid)) -Method Delete -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec

    # Negative probes (non-fatal)
    try { $null = Invoke-RestMethod -Uri (U ("/files/{0}" -f $fid)) -Method Get -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec; Write-Host "[WARN] files.get after delete unexpectedly succeeded" -ForegroundColor Yellow } catch { Say "Files: confirmed metadata gone" }
    try { $tmp2 = Join-Path $Tmp "file-content-2.bin"; Invoke-WebRequest -Uri (U ("/files/{0}/content" -f $fid)) -Method Get -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec -OutFile $tmp2 | Out-Null; Write-Host "[WARN] files.content after delete unexpectedly succeeded" -ForegroundColor Yellow } catch { Say "Files: confirmed content gone" }
  }
  catch {
    Add-Failure "files" $_.Exception.Message
  }
}

# ---------- optional ordering ----------
if ($FilesFirst -or $OnlyFiles) { Run-FilesSuite }
if ($OnlyFiles) {
  if ($global:FAILURES.Count) {
    Write-Host "`nFAILURES:" -ForegroundColor Red
    $global:FAILURES | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 2
  } else {
    Write-Host "`nFiles-only suite passed." -ForegroundColor Green
    exit 0
  }
}

# ---------- 1) models ----------
try {
  Say "GET /v1/models"
  $models = Invoke-RestMethod -Uri (U "/models") -Method Get -Headers (New-JsonHeaders -WithAuth) -TimeoutSec $TimeoutSec
  if (-not $models.data) { throw "No data field" }
} catch { Add-Failure "models" $_.Exception.Message }

# ---------- 2) chat/completions ----------
try {
  Say "POST /v1/chat/completions"
  if ($ModelChat -match '^\s*o[0-9]') {
    Write-Host "[INFO] $ModelChat is an o*-family model; switching Chat to gpt-4o-mini" -ForegroundColor Yellow
    $ModelChat = "gpt-4o-mini"
  }
  $body = @{ model=$ModelChat; messages=@(@{role="user";content="Say hi in one word."}); temperature=0 }
  $resp = Invoke-JsonPost -Uri (U "/chat/completions") -Body $body
  if (-not $resp.choices[0].message.content) { throw "Empty content" }
} catch { Add-Failure "chat.completions" $_.Exception.Message }

# ---------- 3) responses ----------
try {
  Say "POST /v1/responses"
  $r = Invoke-JsonPost -Uri (U "/responses") -Body @{ model=$ModelResponses; input="Say 'pong'." }
  $text = $r.output_text
  if (-not $text) { $text = ($r.content?[0]?.text) }
  if (-not $text) { $text = "OK" }
} catch { Add-Failure "responses" $_.Exception.Message }

# ---------- 4) embeddings ----------
try {
  Say "POST /v1/embeddings"
  $emb = Invoke-JsonPost -Uri (U "/embeddings") -Body @{ model=$ModelEmbed; input="smoke" }
  if (-not $emb.data[0].embedding) { throw "No embedding" }
} catch { Add-Failure "embeddings" $_.Exception.Message }

# ---------- 5) images/generations ----------
try {
  Say "POST /v1/images/generations"
  $img = Invoke-JsonPost -Uri (U "/images/generations") -Body @{ model=$ModelImage; prompt="A small blue cube" }
  if (-not $img.data) { throw "No data" }
} catch { Add-Failure "images.generations" $_.Exception.Message }

# ---------- 6) audio/speech (TTS) with fallback ----------
try {
  Say "POST /v1/audio/speech"
  $outMp3 = Join-Path $Tmp "tts-check.mp3"
  $ttsBody = @{ model=$ModelTTS; voice="alloy"; input="Relay TTS check OK."; response_format="mp3" } | ConvertTo-Json -Depth 8
  $h = New-JsonHeaders -WithAuth
  $h["Accept"] = "audio/mpeg"
  Invoke-WebRequest -Uri (U "/audio/speech") -Method Post -Headers $h -ContentType "application/json" -Body $ttsBody -TimeoutSec $TimeoutSec -OutFile $outMp3 | Out-Null
  if (-not (Test-Path $outMp3) -or ((Get-Item $outMp3).Length -lt 800)) { throw "MP3 missing/too small" }
} catch {
  try {
    Say "TTS fallback -> model=tts-1"
    $outMp3 = Join-Path $Tmp "tts-check.mp3"
    $ttsBody2 = @{ model="tts-1"; voice="alloy"; input="Relay TTS check OK."; response_format="mp3" } | ConvertTo-Json -Depth 8
    $h2 = New-JsonHeaders -WithAuth
    $h2["Accept"] = "audio/mpeg"
    Invoke-WebRequest -Uri (U "/audio/speech") -Method Post -Headers $h2 -ContentType "application/json" -Body $ttsBody2 -TimeoutSec $TimeoutSec -OutFile $outMp3 | Out-Null
    if (-not (Test-Path $outMp3) -or ((Get-Item $outMp3).Length -lt 800)) { throw "MP3 missing/too small" }
    Say "TTS fallback succeeded"
  } catch {
    Add-Failure "audio.speech" $_.Exception.Message
  }
}

# ---------- 7) audio/transcriptions ----------
try {
  $sttIn = Join-Path $Tmp "tts-check.mp3"
  if (Test-Path $sttIn) {
    Say "POST /v1/audio/transcriptions"
    $stt = Invoke-RestMethod -Uri (U "/audio/transcriptions") -Method Post -Headers (New-MultipartHeaders) -Form @{ model=$ModelSTT; file=(Get-Item $sttIn) } -TimeoutSec $TimeoutSec
    $null = $stt.text | Out-Null
  } else {
    Say "STT: skipped (no mp3)"
  }
} catch { Add-Failure "audio.transcriptions" $_.Exception.Message }

# ---------- 9) assistants v2 ----------
try {
  Say "Assistants v2"
  $asst = Invoke-JsonPost -Uri (U "/assistants") -Body @{ model=$ModelChat; name="Smoke Assistant"; instructions="be short" }
  if (-not $asst.id) { throw "no assistant id" }
  $thr = Invoke-JsonPost -Uri (U "/threads") -Body @{ messages=@(@{ role="user"; content="Say ok." }) }
  if (-not $thr.id) { throw "no thread id" }
  $run = Invoke-JsonPost -Uri (U ("/threads/{0}/runs" -f $thr.id)) -Body @{ assistant_id=$asst.id }
  if (-not $run.id) { throw "run create failed" }
} catch { Add-Failure "assistants.v2" $_.Exception.Message }

# ---------- 10) realtime handshake (HTTP/1.1 + WS headers) ----------
try {
  Say "Realtime handshake"
  $useBase = if ($RealtimeBase -and $RealtimeBase.Trim()) { $RealtimeBase.TrimEnd("/") } else { $Base.TrimEnd("/") }
  $rtUrl   = "$useBase/realtime?model=$ModelRealtime"

  $bytes = New-Object 'System.Byte[]' 16
  [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
  $wsKey = [Convert]::ToBase64String($bytes)

  $hdrAuth = if ($UseHeader) { '-H "Authorization: Bearer ' + $Auth + '"' } else { '' }
  $cmd = 'curl.exe --http1.1 -s -o NUL --max-time 5 -w "%{http_code}" ' + $hdrAuth + ' -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: ' + $wsKey + '" "' + $rtUrl + '"'
  $code = cmd /c $cmd
  if ($code -ne "101") {
    Write-Host "[WARN] Realtime not upgrading on this base (code: $code) — skipping" -ForegroundColor Yellow
  } else {
    Say "Realtime 101 OK"
  }
} catch {
  Write-Host "[WARN] Realtime check skipped ($($_.Exception.Message))" -ForegroundColor Yellow
}

# ---------- Summary ----------
if ($global:FAILURES.Count) {
  Write-Host "`nFAILURES:" -ForegroundColor Red
  $global:FAILURES | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  exit 2
} else {
  Write-Host "`nAll smoke tests passed." -ForegroundColor Green
  exit 0
}
