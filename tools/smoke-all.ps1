<# 
Cloudflare Relay Smoke Test (PowerShell 7+)
v1.1 – trims Authorization header, adds -NoClientAuth switch

Changes from v1.0:
- Trim whitespace/newlines on -ApiKey and ignore if empty after trim.
- New -NoClientAuth switch to force *no* Authorization header (useful when relay injects server key).
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [string]$ApiKey = $env:OPENAI_API_KEY,
  [string]$Org = $env:OPENAI_ORG,
  [string]$Project = $env:OPENAI_PROJECT,
  [string]$Model = 'o4-mini',
  [string]$EmbeddingModel = 'text-embedding-3-small',
  [string]$TtsModel = 'gpt-4o-mini-tts',
  [string]$SttModel = 'gpt-4o-mini-transcribe',
  [int]$TimeoutSec = 60,
  [switch]$IncludeHealth,
  [switch]$IncludeAudio,
  [switch]$IncludeImages,
  [switch]$IncludeFiles,
  [switch]$IncludeAssistants,
  [switch]$NoClientAuth
)

function New-Headers {
  param($ApiKey, $Org, $Project)
  $h = @{
    'Accept'        = 'application/json'
    'User-Agent'    = 'relay-smoke/1.1'
  }
  # sanitize key
  if ($ApiKey) {
    $ApiKey = $ApiKey.Trim()
    if (-not [string]::IsNullOrWhiteSpace($ApiKey) -and $ApiKey -notmatch "[\r\n]") {
      $h['Authorization'] = "Bearer $ApiKey"
    }
  }
  if ($Org)     { $h['OpenAI-Organization'] = $Org;  $h['x-openai-organization'] = $Org }
  if ($Project) { $h['OpenAI-Project']      = $Project; $h['x-openai-project'] = $Project }
  return $h
}

function New-Result {
  param([string]$Name, [bool]$Required, [bool]$Success, [int]$StatusCode, [int]$DurationMs, [string]$Message)
  [PSCustomObject]@{
    Name       = $Name
    Required   = $Required
    Success    = $Success
    StatusCode = $StatusCode
    DurationMs = $DurationMs
    Message    = $Message
  }
}

function Invoke-Http {
  param(
    [ValidateSet('GET','POST','DELETE','OPTIONS')][string]$Method,
    [string]$Url,
    [hashtable]$Headers,
    $BodyJson = $null,
    [int]$TimeoutSec = 60,
    [string]$ContentType = 'application/json'
  )
  $resp = $null; $code = 0; $content = $null; $headersOut = $null
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    if ($Method -eq 'GET' -or $Method -eq 'DELETE' -or $Method -eq 'OPTIONS') {
      $resp = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -TimeoutSec $TimeoutSec -ErrorAction Stop
    } else {
      if ($BodyJson -ne $null -and -not ($BodyJson -is [string])) {
        $BodyJson = $BodyJson | ConvertTo-Json -Depth 12 -Compress
      }
      $resp = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -ContentType $ContentType -Body $BodyJson -TimeoutSec $TimeoutSec -ErrorAction Stop
    }
    $code = [int]$resp.StatusCode
    $content = $resp.Content
    $headersOut = $resp.Headers
  } catch {
    $ex = $_.Exception
    try { 
      $code = [int]$ex.Response.StatusCode.value__ 
      $sr = New-Object System.IO.StreamReader($ex.Response.GetResponseStream())
      $content = $sr.ReadToEnd()
    } catch { }
    throw [pscustomobject]@{ StatusCode=$code; Content=$content; ElapsedMs=$sw.ElapsedMilliseconds; Error=$ex.Message }
  } finally {
    $elapsed = $sw.ElapsedMilliseconds
  }
  [pscustomobject]@{ StatusCode=$code; Content=$content; Headers=$headersOut; ElapsedMs=$elapsed }
}

function Write-ResultTable {
  param($Results)
  Write-Host ""
  Write-Host "=== Smoke Results ==="
  $fmt = "{0,-20} {1,-3} {2,-6} {3,4} {4,8}  {5}"
  Write-Host ($fmt -f "Check","Req","OK","Code","Time(ms)","Message")
  Write-Host ("-" * 78)
  foreach ($r in $Results) {
    $ok = if ($r.Success) { "PASS" } else { "FAIL" }
    $req = if ($r.Required) { "Y" } else { "-" }
    Write-Host ($fmt -f $r.Name.Substring(0, [Math]::Min(20,$r.Name.Length)), $req, $ok, $r.StatusCode, $r.DurationMs, $r.Message)
  }
}

if ($BaseUrl.EndsWith('/')) { $BaseUrl = $BaseUrl.TrimEnd('/') }
if ($NoClientAuth) { $ApiKey = $null }

$headers = New-Headers -ApiKey $ApiKey -Org $Org -Project $Project
$results = New-Object System.Collections.Generic.List[object]

# ----- Required: GET /v1/models -----
try {
  $r = Invoke-Http -Method GET -Url "$BaseUrl/v1/models" -Headers $headers -TimeoutSec $TimeoutSec
  $json = $null
  if ($r.Content) { $json = $r.Content | ConvertFrom-Json -ErrorAction Ignore }
  $count = if ($json -and $json.data) { [int]$json.data.Count } else { 0 }
  $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300 -and $count -gt 0)
  $results.Add( (New-Result -Name "GET /models" -Required $true -Success $ok -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message "items=$count") ) | Out-Null
} catch {
  $e = $_.Exception
  $code = if ($e.StatusCode) { $e.StatusCode } else { 0 }
  $msg  = if ($e.Content) { $e.Content } else { $e.Message }
  $results.Add( (New-Result -Name "GET /models" -Required $true -Success $false -StatusCode $code -DurationMs $e.ElapsedMs -Message $msg) ) | Out-Null
}

# ----- Required: POST /v1/chat/completions -----
try {
  $body = @{
    model    = $Model
    messages = @(
      @{ role='system'; content='You are a test probe. Reply with "ok".' },
      @{ role='user';   content='Respond with exactly: ok' }
    )
    temperature = 0
    stream = $false
  }
  $r = Invoke-Http -Method POST -Url "$BaseUrl/v1/chat/completions" -Headers $headers -BodyJson $body -TimeoutSec $TimeoutSec
  $json = $null
  if ($r.Content) { $json = $r.Content | ConvertFrom-Json -ErrorAction Ignore }
  $text = $null
  try { $text = $json.choices[0].message.content } catch {}
  $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300 -and $text -match 'ok')
  $results.Add( (New-Result -Name "POST /chat" -Required $true -Success $ok -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message ("len=" + ($(if ($text) { $text.Length } else { 0 })))) ) | Out-Null
} catch {
  $e = $_.Exception
  $code = if ($e.StatusCode) { $e.StatusCode } else { 0 }
  $msg  = if ($e.Content) { $e.Content } else { $e.Message }
  $results.Add( (New-Result -Name "POST /chat" -Required $true -Success $false -StatusCode $code -DurationMs $e.ElapsedMs -Message $msg) ) | Out-Null
}

# ----- Required: POST /v1/embeddings -----
try {
  $body = @{
    model = $EmbeddingModel
    input = 'Hello from the relay smoke test'
  }
  $r = Invoke-Http -Method POST -Url "$BaseUrl/v1/embeddings" -Headers $headers -BodyJson $body -TimeoutSec $TimeoutSec
  $json = $null
  if ($r.Content) { $json = $r.Content | ConvertFrom-Json -ErrorAction Ignore }
  $vecLen = 0
  try { $vecLen = [int]$json.data[0].embedding.Count } catch {}
  $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300 -and $vecLen -gt 0)
  $results.Add( (New-Result -Name "POST /embeddings" -Required $true -Success $ok -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message "dim=$vecLen") ) | Out-Null
} catch {
  $e = $_.Exception
  $code = if ($e.StatusCode) { $e.StatusCode } else { 0 }
  $msg  = if ($e.Content) { $e.Content } else { $e.Message }
  $results.Add( (New-Result -Name "POST /embeddings" -Required $true -Success $false -StatusCode $code -DurationMs $e.ElapsedMs -Message $msg) ) | Out-Null
}

# ----- Required: CORS preflight (OPTIONS) for /v1/chat/completions -----
try {
  $corsHeaders = @{
    'Origin'                          = 'https://example.com'
    'Access-Control-Request-Method'   = 'POST'
    'Access-Control-Request-Headers'  = 'authorization, content-type'
  }
  $r = Invoke-Http -Method OPTIONS -Url "$BaseUrl/v1/chat/completions" -Headers $corsHeaders -TimeoutSec $TimeoutSec
  $allowOrigin  = $r.Headers['Access-Control-Allow-Origin']
  $allowHeaders = $r.Headers['Access-Control-Allow-Headers']
  $ok = ($r.StatusCode -in 200,204) -and $allowOrigin -ne $null -and ($allowHeaders -match '(?i)authorization') -and ($allowHeaders -match '(?i)content-type')
  $msg = "Allow-Origin=${allowOrigin}; Allow-Headers=${allowHeaders}"
  $results.Add( (New-Result -Name "OPTIONS /chat (CORS)" -Required $true -Success $ok -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message $msg) ) | Out-Null
} catch {
  $e = $_.Exception
  $code = if ($e.StatusCode) { $e.StatusCode } else { 0 }
  $msg  = if ($e.Content) { $e.Content } else { $e.Message }
  $results.Add( (New-Result -Name "OPTIONS /chat (CORS)" -Required $true -Success $false -StatusCode $code -DurationMs $e.ElapsedMs -Message $msg) ) | Out-Null
}

# ----- Optional: /health -----
if ($IncludeHealth) {
  try {
    $r = Invoke-Http -Method GET -Url "$BaseUrl/health" -Headers (New-Headers -ApiKey $null -Org $null -Project $null) -TimeoutSec $TimeoutSec
    $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
    $results.Add( (New-Result -Name "GET /health" -Required $false -Success $ok -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message "health check") ) | Out-Null
  } catch {
    $e = $_.Exception
    $code = if ($e.StatusCode) { $e.StatusCode } else { 0 }
    $msg  = if ($e.Content) { $e.Content } else { $e.Message }
    $results.Add( (New-Result -Name "GET /health" -Required $false -Success $false -StatusCode $code -DurationMs $e.ElapsedMs -Message $msg) ) | Out-Null
  }
}

# ----- Optional: Audio (TTS -> MP3), then STT -----
$ttsFile = Join-Path $PWD "smoke-tts.mp3"
if ($IncludeAudio) {
  try {
    $ttsHeaders = New-Headers -ApiKey $ApiKey -Org $Org -Project $Project
    $ttsHeaders['Accept'] = 'audio/mpeg'
    $body = @{
      model  = $TtsModel
      input  = 'This is a relay text-to-speech test.'
      voice  = 'alloy'
      format = 'mp3'
    }
    $jsonBody = $body | ConvertTo-Json -Depth 6 -Compress
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Invoke-WebRequest -Method POST -Uri "$BaseUrl/v1/audio/speech" -Headers $ttsHeaders -ContentType 'application/json' -Body $jsonBody -OutFile $ttsFile -TimeoutSec $TimeoutSec -ErrorAction Stop | Out-Null
    $elapsed = $sw.ElapsedMilliseconds
    $size = (Get-Item $ttsFile -ErrorAction Stop).Length
    $ok = ($size -gt 1024)
    $results.Add( (New-Result -Name "POST /audio/speech" -Required $false -Success $ok -StatusCode 200 -DurationMs $elapsed -Message "bytes=$size -> $ttsFile") ) | Out-Null
  } catch {
    $e = $_.Exception
    $results.Add( (New-Result -Name "POST /audio/speech" -Required $false -Success $false -StatusCode 0 -DurationMs 0 -Message $e.Message) ) | Out-Null
  }

  if (Test-Path $ttsFile) {
    try {
      $fs = [System.IO.File]::OpenRead($ttsFile)
      $content = New-Object System.Net.Http.StreamContent($fs)
      $content.Headers.ContentType = 'audio/mpeg'
      $mp = New-Object System.Net.Http.MultipartFormDataContent
      $mp.Add($content, 'file', [System.IO.Path]::GetFileName($ttsFile))
      $mp.Add( (New-Object System.Net.Http.StringContent($SttModel)), 'model')

      $handler = New-Object System.Net.Http.HttpClientHandler
      $client  = New-Object System.Net.Http.HttpClient($handler)
      $client.Timeout = [TimeSpan]::FromSeconds($TimeoutSec)
      $client.DefaultRequestHeaders.Add('User-Agent','relay-smoke/1.1')
      if ($ApiKey) { $client.DefaultRequestHeaders.Add('Authorization', "Bearer $($ApiKey.Trim())") }
      if ($Org)     { $client.DefaultRequestHeaders.Add('OpenAI-Organization', $Org) ; $client.DefaultRequestHeaders.Add('x-openai-organization',$Org) }
      if ($Project) { $client.DefaultRequestHeaders.Add('OpenAI-Project', $Project)   ; $client.DefaultRequestHeaders.Add('x-openai-project',$Project) }

      $sw = [System.Diagnostics.Stopwatch]::StartNew()
      $resp = $client.PostAsync("$BaseUrl/v1/audio/transcriptions", $mp).GetAwaiter().GetResult()
      $elapsed = $sw.ElapsedMilliseconds
      $status = [int]$resp.StatusCode
      $txt = $resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
      $ok  = ($status -ge 200 -and $status -lt 300 -and $txt.Length -gt 0)
      $results.Add( (New-Result -Name "POST /audio/transc." -Required $false -Success $ok -StatusCode $status -DurationMs $elapsed -Message ("len=" + $txt.Length)) ) | Out-Null

      $client.Dispose(); $handler.Dispose(); $fs.Dispose()
    } catch {
      $e = $_.Exception
      $results.Add( (New-Result -Name "POST /audio/transc." -Required $false -Success $false -StatusCode 0 -DurationMs 0 -Message $e.Message) ) | Out-Null
    }
  }
}

# ----- Optional: Images -----
$imgFile = Join-Path $PWD "smoke-image.png"
if ($IncludeImages) {
  try {
    $body = @{
      model = 'gpt-image-1'
      prompt = 'A 128x128 red ball on white background, minimalistic.'
      size = '256x256'
      response_format = 'b64_json'
    }
    $r = Invoke-Http -Method POST -Url "$BaseUrl/v1/images/generations" -Headers $headers -BodyJson $body -TimeoutSec ($TimeoutSec + 30)
    $json = $null
    if ($r.Content) { $json = $r.Content | ConvertFrom-Json -ErrorAction Ignore }
    $b64 = $json.data[0].b64_json
    if ($b64) {
      [IO.File]::WriteAllBytes($imgFile, [Convert]::FromBase64String($b64))
    }
    $size = if (Test-Path $imgFile) { (Get-Item $imgFile).Length } else { 0 }
    $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300 -and $size -gt 1024)
    $results.Add( (New-Result -Name "POST /images/gen" -Required $false -Success $ok -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message "bytes=$size -> $imgFile") ) | Out-Null
  } catch {
    $e = $_.Exception
    $code = if ($e.StatusCode) { $e.StatusCode } else { 0 }
    $msg  = if ($e.Content) { $e.Content } else { $e.Message }
    $results.Add( (New-Result -Name "POST /images/gen" -Required $false -Success $false -StatusCode $code -DurationMs 0 -Message $msg) ) | Out-Null
  }
}

# ----- Optional: Files API -----
if ($IncludeFiles) {
  $tmpJsonl = Join-Path $PWD "smoke-file.jsonl"
  try {
    @(
      '{"prompt":"hello","completion":"world"}'
      '{"prompt":"foo","completion":"bar"}'
    ) | Set-Content -Path $tmpJsonl -Encoding utf8

    $fs = [System.IO.File]::OpenRead($tmpJsonl)
    $fileContent = New-Object System.Net.Http.StreamContent($fs)
    $fileContent.Headers.ContentType = 'application/json'
    $purposeContent = New-Object System.Net.Http.StringContent('assistants')
    $purposeContent.Headers.ContentType = 'text/plain'

    $mp = New-Object System.Net.Http.MultipartFormDataContent
    $mp.Add($fileContent, 'file', [System.IO.Path]::GetFileName($tmpJsonl))
    $mp.Add($purposeContent, 'purpose')

    $handler = New-Object System.Net.Http.HttpClientHandler
    $client  = New-Object System.Net.Http.HttpClient($handler)
    $client.Timeout = [TimeSpan]::FromSeconds($TimeoutSec)
    $client.DefaultRequestHeaders.Add('User-Agent','relay-smoke/1.1')
    if ($ApiKey) { $client.DefaultRequestHeaders.Add('Authorization', "Bearer $($ApiKey.Trim())") }
    if ($Org)     { $client.DefaultRequestHeaders.Add('OpenAI-Organization', $Org); $client.DefaultRequestHeaders.Add('x-openai-organization',$Org) }
    if ($Project) { $client.DefaultRequestHeaders.Add('OpenAI-Project', $Project);   $client.DefaultRequestHeaders.Add('x-openai-project',$Project) }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $resp = $client.PostAsync("$BaseUrl/v1/files", $mp).GetAwaiter().GetResult()
    $elapsed = $sw.ElapsedMilliseconds
    $status = [int]$resp.StatusCode
    $txt = $resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    $upload = $null
    try { $upload = $txt | ConvertFrom-Json } catch {}
    $fileId = $upload.id
    $ok = ($status -ge 200 -and $status -lt 300 -and $fileId)
    $results.Add( (New-Result -Name "POST /files (up)" -Required $false -Success $ok -StatusCode $status -DurationMs $elapsed -Message "id=$fileId") ) | Out-Null
    $fs.Dispose()

    if ($ok) {
      $r = Invoke-Http -Method GET -Url "$BaseUrl/v1/files" -Headers $headers -TimeoutSec $TimeoutSec
      $json = $null; if ($r.Content) { $json = $r.Content | ConvertFrom-Json -ErrorAction Ignore }
      $count = if ($json.data) { [int]$json.data.Count } else { 0 }
      $results.Add( (New-Result -Name "GET /files (ls)" -Required $false -Success ($count -ge 1) -StatusCode $r.StatusCode -DurationMs $r.ElapsedMs -Message "items=$count") ) | Out-Null

      $r2 = Invoke-Http -Method GET -Url "$BaseUrl/v1/files/$fileId/content" -Headers $headers -TimeoutSec $TimeoutSec
      $bytes = [System.Text.Encoding]::UTF8.GetBytes([string]$r2.Content)
      $ok2 = ($r2.StatusCode -ge 200 -and $r2.StatusCode -lt 300 -and $bytes.Length -gt 0)
      $results.Add( (New-Result -Name "GET /files/{id}" -Required $false -Success $ok2 -StatusCode $r2.StatusCode -DurationMs $r2.ElapsedMs -Message ("bytes=" + $bytes.Length)) ) | Out-Null

      $r3 = Invoke-Http -Method DELETE -Url "$BaseUrl/v1/files/$fileId" -Headers $headers -TimeoutSec $TimeoutSec
      $ok3 = ($r3.StatusCode -ge 200 -and $r3.StatusCode -lt 300)
      $results.Add( (New-Result -Name "DEL /files/{id}" -Required $false -Success $ok3 -StatusCode $r3.StatusCode -DurationMs $r3.ElapsedMs -Message "deleted") ) | Out-Null
    }

    $client.Dispose(); $handler.Dispose()
  } catch {
    $e = $_.Exception
    $results.Add( (New-Result -Name "Files API flow" -Required $false -Success $false -StatusCode 0 -DurationMs 0 -Message $e.Message) ) | Out-Null
  } finally {
    if (Test-Path $tmpJsonl) { Remove-Item $tmpJsonl -Force -ErrorAction SilentlyContinue }
  }
}

# ----- Optional: Assistants v2 -----
if ($IncludeAssistants) {
  try {
    $asstBody = @{
      model = $Model
      name  = 'smoke-assistant'
      instructions = 'You are a test assistant.'
      tools = @()
    }
    $rA = Invoke-Http -Method POST -Url "$BaseUrl/v1/assistants" -Headers $headers -BodyJson $asstBody -TimeoutSec $TimeoutSec
    $asst = $null; if ($rA.Content) { $asst = $rA.Content | ConvertFrom-Json -ErrorAction Ignore }
    $asstId = $asst.id

    $threadBody = @{ messages = @(@{ role='user'; content='Say: ok' }) }
    $rT = Invoke-Http -Method POST -Url "$BaseUrl/v1/threads" -Headers $headers -BodyJson $threadBody -TimeoutSec $TimeoutSec
    $thread = $null; if ($rT.Content) { $thread = $rT.Content | ConvertFrom-Json -ErrorAction Ignore }
    $threadId = $thread.id

    $runBody = @{ assistant_id = $asstId }
    $rR = Invoke-Http -Method POST -Url "$BaseUrl/v1/threads/$threadId/runs" -Headers $headers -BodyJson $runBody -TimeoutSec $TimeoutSec
    $run = $null; if ($rR.Content) { $run = $rR.Content | ConvertFrom-Json -ErrorAction Ignore }
    $runId = $run.id

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds([Math]::Max(30,$TimeoutSec))
    $final = $null; $status = $run.status
    while ([DateTimeOffset]::UtcNow -lt $deadline) {
      Start-Sleep -Milliseconds 600
      $rG = Invoke-Http -Method GET -Url "$BaseUrl/v1/threads/$threadId/runs/$runId" -Headers $headers -TimeoutSec $TimeoutSec
      $final = $null; if ($rG.Content) { $final = $rG.Content | ConvertFrom-Json -ErrorAction Ignore }
      $status = $final.status
      if ($status -in 'completed','failed','cancelled','expired') { break }
    }

    $ok = ($status -eq 'completed')
    $results.Add( (New-Result -Name "Assistants v2 run" -Required $false -Success $ok -StatusCode 200 -DurationMs 0 -Message "status=$status") ) | Out-Null

    try {
      $rM = Invoke-Http -Method GET -Url "$BaseUrl/v1/threads/$threadId/messages" -Headers $headers -TimeoutSec $TimeoutSec
      $j = $null; if ($rM.Content) { $j = $rM.Content | ConvertFrom-Json -ErrorAction Ignore }
      $cnt = if ($j.data) { [int]$j.data.Count } else { 0 }
      $results.Add( (New-Result -Name "Assistants msgs" -Required $false -Success ($cnt -ge 1) -StatusCode $rM.StatusCode -DurationMs $rM.ElapsedMs -Message "items=$cnt") ) | Out-Null
    } catch {}

  } catch {
    $e = $_.Exception
    $results.Add( (New-Result -Name "Assistants flow" -Required $false -Success $false -StatusCode 0 -DurationMs 0 -Message $e.Message) ) | Out-Null
  }
}

Write-ResultTable -Results $results
$failedRequired = $results | Where-Object { $_.Required -and -not $_.Success }
if ($failedRequired) {
  Write-Host ""
  Write-Host "Required checks failed. Exiting with code 1." -ForegroundColor Red
  exit 1
} else {
  Write-Host ""
  Write-Host "All required checks passed." -ForegroundColor Green
  exit 0
}
