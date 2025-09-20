param(
  [Parameter(Mandatory=$true)][string]$Base,                    # e.g. https://relay.example.com
  [string]$ApiKey = $env:OPENAI_API_KEY,                        # set env var or pass here
  [string]$ModelText = "gpt-4o-mini",
  [string]$ModelImage = "gpt-image-1",
  [string]$ModelTTS = "gpt-4o-mini-tts",
  [string]$ModelSTT = "whisper-1",                              # keep compatibility
  [switch]$RunImages,
  [switch]$RunTTS,
  [switch]$RunSTT,
  [string]$SampleAudio = ".\tts.mp3",                        # used if -RunSTT and file exists
  [int]$PollSeconds = 45,
  [int]$StreamSeconds = 20
)

$ErrorActionPreference = 'Stop'
if (-not $ApiKey) { throw "API key missing. Pass -ApiKey or set OPENAI_API_KEY." }

$log = Join-Path $PSScriptRoot "run_result.txt"
function Write-Result([string]$label, [string]$status, [string]$note="") {
  $line = "{0} | {1} | {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $label, ($status + $(if($note){ " ($note)" } else { "" }))
  Add-Content -Path $log -Value $line
  Write-Host $line
}

function PostJsonIRM($url, $bodyObj) {
  $json = $bodyObj | ConvertTo-Json -Depth 20
  return Invoke-RestMethod -Method POST -Uri $url -Headers @{ "Authorization"="Bearer $ApiKey"; "Content-Type"="application/json" } -Body $json -TimeoutSec 120
}

function PostJsonCurl([string]$url, [string]$json) {
  $args = @("-s", "-X","POST", $url, "-H","Authorization: Bearer $ApiKey", "-H","Content-Type: application/json", "-d", $json)
  $out = & curl.exe @args
  if ($LASTEXITCODE -ne 0) { throw "curl exit code $LASTEXITCODE" }
  return $out
}

# 1) /v1/completions (shim) → IRM + curl should PASS
try {
  $label = "/v1/completions (shim) → IRM + curl should PASS"
  $url = "$Base/v1/completions"
  # IRM
  $irm = PostJsonIRM $url @{ model = $ModelText; prompt = "Say OK"; max_tokens = 8 }
  if (-not $irm.choices) { throw "IRM: choices missing" }
  # curl
  $json = '{"model":"' + $ModelText + '","prompt":"Say OK","max_tokens":8}'
  $curlOut = PostJsonCurl $url $json
  $curlParsed = $null; try { $curlParsed = $curlOut | ConvertFrom-Json } catch { }
  if (-not $curlParsed.choices) { throw "curl: choices missing" }
  Write-Result $label "PASS"
} catch { Write-Result "/v1/completions (shim)" "FAIL" $_.Exception.Message }

# 2) /v1/edits (shim) → IRM + curl should PASS
try {
  $label = "/v1/edits (shim) → IRM + curl should PASS"
  $url = "$Base/v1/edits"
  $irm = PostJsonIRM $url @{ model = $ModelText; input = "Ths is a tst."; instruction = "Fix spelling." }
  if (-not $irm.choices) { throw "IRM: choices missing" }
  $json = '{"model":"' + $ModelText + '","input":"Ths is a tst.","instruction":"Fix spelling."}'
  $curlOut = PostJsonCurl $url $json
  $curlParsed = $null; try { $curlParsed = $curlOut | ConvertFrom-Json } catch { }
  if (-not $curlParsed.choices) { throw "curl: choices missing" }
  Write-Result $label "PASS"
} catch { Write-Result "/v1/edits (shim)" "FAIL" $_.Exception.Message }

# 3) /v1/responses (tools) → IRM PASS with tool call present
try {
  $label = "/v1/responses (tools) → IRM PASS with tool call present"
  $url = "$Base/v1/responses"
  $tools = @(
    @{
      type="function"; name="get_time"; description="Return current time in ISO8601"; parameters=@{ type="object"; properties=@{}; required=@() }
    }
  )
  $body = @{
    model = $ModelText
    input = "Call get_time, then say 'done'."
    tools = $tools
  }
  $irm = PostJsonIRM $url $body
  $hasTool = ($irm.output | ConvertTo-Json -Depth 30) -match 'tool_call|tool_calls'
  if (-not $hasTool) { throw "tool call not detected in response.output" }
  Write-Result $label "PASS"
} catch { Write-Result "/v1/responses (tools)" "FAIL" $_.Exception.Message }

# 4) /v1/background → kick + poll to terminal state
try {
  $label = "/v1/background → kick + poll to terminal state"
  $kickUrl = "$Base/v1/background"
  $kick = PostJsonIRM $kickUrl @{ model = $ModelText; input = "Return the word PONG."; background = $true }
  $id = $kick.id
  if (-not $id) { throw "kick missing id" }
  $pollUrl = "$Base/v1/background/$id"
  $deadline = (Get-Date).AddSeconds($PollSeconds)
  $status = $kick.status
  while ((Get-Date) -lt $deadline -and ($status -in @($null,"queued","running","in_progress"))) {
    Start-Sleep -Seconds 2
    $res = Invoke-RestMethod -Method GET -Uri $pollUrl -Headers @{ "Authorization"="Bearer $ApiKey" }
    $status = $res.status
  }
  if ($status -in @("completed","succeeded","failed","cancelled")) {
    Write-Result $label "PASS" "status=$status"
  } else {
    throw "timeout waiting for terminal state (last=$status)"
  }
} catch { Write-Result "/v1/background" "FAIL" $_.Exception.Message }

# 5) Streaming smoke → curl -sN receives chunks
try {
  $label = "Streaming smoke → curl -sN receives chunks"
  $url = "$Base/v1/responses"
  $json = '{"model":"' + $ModelText + '","input":"Stream a tiny poem.","stream":true}'
  $args = @("-sN","-X","POST",$url,"-H","Authorization: Bearer $ApiKey","-H","Content-Type: application/json","-d",$json,"--max-time",$StreamSeconds)
  $out = & curl.exe @args
  if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
  if ($out -match 'data:\s*') {
    Write-Result $label "PASS"
  } else {
    throw "no SSE 'data:' lines observed"
  }
} catch { Write-Result "Streaming smoke" "FAIL" $_.Exception.Message }

# Optional: Images
if ($RunImages) {
  try {
    $label = "Optional re-runs: Images"
    $url = "$Base/v1/images/edits"   # try generation first; if your relay uses /v1/images/generations, switch:
    $urlGen = "$Base/v1/images/generations"
    $body = @{ model=$ModelImage; prompt="a small monochrome geometric logo"; size="256x256"; response_format="b64_json" }
    try {
      $irm = PostJsonIRM $urlGen $body
    } catch {
      $irm = PostJsonIRM $url $body
    }
    $b64 = $irm.data[0].b64_json
    if (-not $b64) { throw "b64_json missing" }
    $bytes = [Convert]::FromBase64String($b64)
    $outPath = Join-Path $PSScriptRoot "image_256.png"
    [IO.File]::WriteAllBytes($outPath,$bytes)
    Write-Result $label "PASS" "saved $(Split-Path $outPath -Leaf)"
  } catch { Write-Result "Images" "FAIL" $_.Exception.Message }
}

# Optional: TTS
if ($RunTTS) {
  try {
    $label = "Optional re-runs: TTS"
    $url = "$Base/v1/audio/speech"
    $irm = PostJsonIRM $url @{ model=$ModelTTS; voice="alloy"; input="Hello from the relay TTS check."; format="mp3" }
    $bytes = [Convert]::FromBase64String($irm.audio ?? "")
    if (-not $bytes) { throw "audio bytes missing" }
    $outPath = Join-Path $PSScriptRoot "tts_output.mp3"
    [IO.File]::WriteAllBytes($outPath,$bytes)
    Write-Result $label "PASS" "saved $(Split-Path $outPath -Leaf)"
  } catch { Write-Result "TTS" "FAIL" $_.Exception.Message }
}

# Optional: STT
if ($RunSTT) {
  try {
    $label = "Optional re-runs: STT"
    if (-not (Test-Path $SampleAudio)) { throw "sample audio not found: $SampleAudio" }
    $url = "$Base/v1/audio/transcriptions"
    $boundary = [System.Guid]::NewGuid().ToString("N")
    $fileBytes = [IO.File]::ReadAllBytes($SampleAudio)
    $fileB64 = [Convert]::ToBase64String($fileBytes)

    # Use curl.exe for multipart/form-data (simpler)
    $args = @(
      "-s","-X","POST",$url,
      "-H","Authorization: Bearer $ApiKey",
      "-H","Content-Type: multipart/form-data",
      "-F","model=$ModelSTT",
      "-F","file=@$SampleAudio"
    )
    $out = & curl.exe @args
    if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
    $j = $null; try { $j = $out | ConvertFrom-Json } catch { }
    if (-not $j.text) { throw "transcript text missing" }
    Write-Result $label "PASS" ("transcript: " + ($j.text.Substring(0, [Math]::Min(40,$j.text.Length)) + '...'))
  } catch { Write-Result "STT" "FAIL" $_.Exception.Message }
}

# 6) Moderations (blocked by design)
Write-Result "/v1/moderations via relay" "SKIP" "blocked by design"
