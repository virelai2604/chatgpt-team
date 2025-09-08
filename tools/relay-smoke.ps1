<#
.SYNOPSIS
  End-to-end smoke tests for an OpenAI-compatible relay (Cloudflare Worker, FastAPI proxy, etc.).
.DESCRIPTION
  Runs a minimal-but-useful set of API checks:
    1) GET /v1/models
    2) POST /v1/chat/completions
    3) POST /v1/embeddings
    4) POST /v1/images/generations (optional)
    5) POST /v1/audio/speech  (Text-to-Speech; optional)
    6) POST /v1/audio/transcriptions (Speech-to-Text; optional)
    7) Files API: upload -> list -> retrieve -> delete (optional)
  Each step prints PASS/FAIL and returns non-zero exit code if any required step fails.
.PARAMETER BaseUrl
  Base URL for the relay (e.g., https://chatgpt-team.pages.dev or http://localhost:8787).
.PARAMETER ApiKey
  API key to send in Authorization header. Defaults to $env:OPENAI_API_KEY.
.PARAMETER SkipOptional
  If provided, skips optional tests (images, tts, stt, files).
.EXAMPLE
  .\relay-smoke.ps1 -BaseUrl https://chatgpt-team.pages.dev -ApiKey $env:OPENAI_API_KEY
#>

param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [string]$ApiKey = $env:OPENAI_API_KEY,
  [switch]$SkipOptional
)

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  Write-Error "ApiKey is empty. Provide -ApiKey or set OPENAI_API_KEY."
  exit 2
}

# Ensure no trailing slash
if ($BaseUrl.EndsWith("/")) { $BaseUrl = $BaseUrl.TrimEnd("/") }

$Headers = @{
  "Authorization" = "Bearer $ApiKey"
  "Content-Type"  = "application/json"
}

$ErrorActionPreference = "Stop"
$global:FAILURES = @()

function Write-StepResult($Name, $Succeeded, $Details) {
  if ($Succeeded) {
    Write-Host "[PASS] $Name" -ForegroundColor Green
  } else {
    Write-Host "[FAIL] $Name -> $Details" -ForegroundColor Red
    $global:FAILURES += "$Name: $Details"
  }
}

function Invoke-JsonPost($Uri, $BodyObj, [switch]$RawResponse) {
  $json = $BodyObj | ConvertTo-Json -Depth 10 -Compress
  try {
    $resp = Invoke-RestMethod -Uri $Uri -Headers $Headers -Method Post -Body $json
    if ($RawResponse) { return $resp } else { return $resp }
  }
  catch {
    throw $_
  }
}

# Create downloads folder
$dl = Join-Path -Path $PSScriptRoot -ChildPath "downloads"
if (-not (Test-Path $dl)) { New-Item -ItemType Directory -Path $dl | Out-Null }

# 1) Models
try {
  $models = Invoke-RestMethod -Uri "$BaseUrl/v1/models" -Headers @{ "Authorization"="Bearer $ApiKey" } -Method Get
  $ok = $models -and $models.data
  Write-StepResult "GET /v1/models" $ok "No 'data' array in response"
} catch {
  Write-StepResult "GET /v1/models" $false $_.Exception.Message
}

# Helper to pick a reasonable default model names
$chatModel = "gpt-4o-mini"
$embedModel = "text-embedding-3-small"
$ttsModel   = "gpt-4o-mini-tts"

# 2) Chat Completions
try {
  $chatBody = @{
    model = $chatModel
    messages = @(
      @{ role = "system"; content = "You are a helpful assistant." },
      @{ role = "user";   content = "Say 'pong'." }
    )
    temperature = 0
  }
  $chat = Invoke-JsonPost "$BaseUrl/v1/chat/completions" $chatBody
  $content = $chat.choices[0].message.content
  $ok = $content -and ($content -match "pong")
  Write-StepResult "POST /v1/chat/completions" $ok ("Unexpected reply: " + ($content | Out-String))
} catch {
  Write-StepResult "POST /v1/chat/completions" $false $_.Exception.Message
}

# 3) Embeddings
try {
  $embedBody = @{
    model = $embedModel
    input = @("hello world")
  }
  $emb = Invoke-JsonPost "$BaseUrl/v1/embeddings" $embedBody
  $ok = $emb -and $emb.data -and $emb.data[0].embedding
  Write-StepResult "POST /v1/embeddings" $ok "No embedding returned"
} catch {
  Write-StepResult "POST /v1/embeddings" $false $_.Exception.Message
}

if (-not $SkipOptional) {
  # 4) Images (generations)
  try {
    $imgBody = @{
      model   = "gpt-image-1"
      prompt  = "simple black square icon"
      size    = "256x256"
      response_format = "b64_json"
    }
    $img = Invoke-JsonPost "$BaseUrl/v1/images/generations" $imgBody
    $b64 = $img.data[0].b64_json
    if ($b64) {
      $bytes = [Convert]::FromBase64String($b64)
      $imgPath = Join-Path $dl "smoke-image.png"
      [IO.File]::WriteAllBytes($imgPath, $bytes)
      Write-StepResult "POST /v1/images/generations" $true "Saved to $imgPath"
    } else {
      Write-StepResult "POST /v1/images/generations" $false "No b64 image data"
    }
  } catch {
    Write-StepResult "POST /v1/images/generations" $false $_.Exception.Message
  }

  # 5) TTS (audio/speech)
  try {
    $ttsBody = @{
      model = $ttsModel
      input = "Hello from the relay smoke test."
      voice = "alloy"
      format = "mp3"
    }
    $ttsJson = $ttsBody | ConvertTo-Json -Depth 10 -Compress
    $ttsPath = Join-Path $dl "smoke-tts.mp3"
    $ttsResp = Invoke-WebRequest -Uri "$BaseUrl/v1/audio/speech" -Headers @{ "Authorization"="Bearer $ApiKey"; "Content-Type"="application/json" } -Method Post -Body $ttsJson -OutFile $ttsPath
    $ok = Test-Path $ttsPath -and ((Get-Item $ttsPath).Length -gt 0)
    Write-StepResult "POST /v1/audio/speech" $ok ("Saved to $ttsPath")
  } catch {
    Write-StepResult "POST /v1/audio/speech" $false $_.Exception.Message
  }

  # 6) STT (audio/transcriptions) — use a tiny WAV generated on the fly
  try {
    $wavPath = Join-Path $dl "beep.wav"
    # Generate a 0.2s silent wav to keep the payload tiny (still valid audio file)
    $fs = New-Object IO.FileStream($wavPath, [IO.FileMode]::Create, [IO.FileAccess]::Write)
    $bw = New-Object IO.BinaryWriter($fs)
    # Write minimal 16-bit PCM mono 8kHz WAV header + data (silence)
    $sampleRate = 8000
    $durationSec = 1
    $numSamples = $sampleRate * $durationSec
    $subchunk2Size = $numSamples * 2
    $chunkSize = 36 + $subchunk2Size
    # RIFF header
    $bw.Write([byte[]][char[]]"RIFF")
    $bw.Write([BitConverter]::GetBytes([int]$chunkSize))
    $bw.Write([byte[]][char[]]"WAVE")
    # fmt subchunk
    $bw.Write([byte[]][char[]]"fmt ")
    $bw.Write([BitConverter]::GetBytes([int]16))   # Subchunk1Size
    $bw.Write([BitConverter]::GetBytes([short]1))  # PCM
    $bw.Write([BitConverter]::GetBytes([short]1))  # mono
    $bw.Write([BitConverter]::GetBytes([int]$sampleRate))
    $bw.Write([BitConverter]::GetBytes([int]($sampleRate*2)))
    $bw.Write([BitConverter]::GetBytes([short]2))
    $bw.Write([BitConverter]::GetBytes([short]16))
    # data subchunk
    $bw.Write([byte[]][char[]]"data")
    $bw.Write([BitConverter]::GetBytes([int]$subchunk2Size))
    # write silence
    $bw.Write((New-Object byte[]($subchunk2Size)))
    $bw.Close(); $fs.Close()

    $sttForm = @{
      model = "whisper-1"
    }
    $formFields = @{
      "model" = "whisper-1"
    }
    $sttResp = Invoke-WebRequest -Uri "$BaseUrl/v1/audio/transcriptions" -Headers @{ "Authorization"="Bearer $ApiKey" } -Method Post -InFile $wavPath -ContentType "audio/wav; charset=binary" -UseBasicParsing
    # Some relays require multipart form; attempt fallback if needed
    if ($sttResp.StatusCode -ge 400) {
      $sttResp = Invoke-WebRequest -Uri "$BaseUrl/v1/audio/transcriptions" -Headers @{ "Authorization"="Bearer $ApiKey" } -Method Post -Form @{ model="whisper-1"; file=Get-Item $wavPath }
    }
    $ok = $sttResp.StatusCode -in 200..299
    Write-StepResult "POST /v1/audio/transcriptions" $ok ("HTTP " + $sttResp.StatusCode)
  } catch {
    Write-StepResult "POST /v1/audio/transcriptions" $false $_.Exception.Message
  }

  # 7) Files API: upload/list/retrieve/delete (JSONL tiny file)
  try {
    $jsonlPath = Join-Path $dl "tiny.jsonl"
    Set-Content -LiteralPath $jsonlPath -Value '{"text":"hello"}' -NoNewline

    $upload = Invoke-WebRequest -Uri "$BaseUrl/v1/files" -Headers @{ "Authorization"="Bearer $ApiKey" } -Method Post -Form @{
      purpose = "assistants"
      file = Get-Item $jsonlPath
    }
    $uploadJson = $upload.Content | ConvertFrom-Json
    $fileId = $uploadJson.id
    $okUp = $fileId -ne $null
    Write-StepResult "POST /v1/files (upload)" $okUp ("file_id=" + $fileId)

    $list = Invoke-RestMethod -Uri "$BaseUrl/v1/files" -Headers @{ "Authorization"="Bearer $ApiKey" } -Method Get
    $okList = $list.data.Count -ge 1
    Write-StepResult "GET /v1/files (list)" $okList "No files returned"

    if ($fileId) {
      $contentPath = Join-Path $dl "downloaded.jsonl"
      Invoke-WebRequest -Uri "$BaseUrl/v1/files/$fileId/content" -Headers @{ "Authorization"="Bearer $ApiKey" } -OutFile $contentPath | Out-Null
      $okGet = (Test-Path $contentPath) -and ((Get-Item $contentPath).Length -gt 0)
      Write-StepResult "GET /v1/files/{id}/content" $okGet "No content saved"

      $del = Invoke-RestMethod -Uri "$BaseUrl/v1/files/$fileId" -Headers @{ "Authorization"="Bearer $ApiKey" } -Method Delete
      $okDel = $del.deleted -eq $true
      Write-StepResult "DELETE /v1/files/{id}" $okDel "Delete flag not true"
    }
  } catch {
    Write-StepResult "Files API sequence" $false $_.Exception.Message
  }
}

if ($global:FAILURES.Count -gt 0) {
  Write-Host "`nOne or more checks failed:" -ForegroundColor Yellow
  $global:FAILURES | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
  exit 1
} else {
  Write-Host "`nAll required checks passed." -ForegroundColor Green
  exit 0
}
