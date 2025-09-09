param(
  [string]$RepoRoot = "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team",
  [string]$Base,                 # optional override for REST base (ends with /v1)
  [string]$RealtimeBase,         # optional override for WS (ends with /v1)
  [string]$Auth = "dev",         # "dev" to auto-pick key; or pass an actual sk-...
  [int]$TimeoutSec = 60,
  [string]$ModelChat = "gpt-4o-mini"
)

$ErrorActionPreference = "Stop"
function Read-DotEnv($path) {
  if (!(Test-Path $path)) { return @{} }
  $m = @{}
  Get-Content $path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $kv = $line -split "=",2
    if ($kv.Count -eq 2) { $m[$kv[0].Trim()] = $kv[1].Trim().Trim('"') }
  }
  return $m
}

# 1) Locate repo + .dev.vars
Set-Location $RepoRoot
$dotenv = Read-DotEnv (Join-Path $RepoRoot ".dev.vars")

# 2) Compute endpoints
$LiveRoot = "https://chatgpt-team.pages.dev"
$Live     = "$LiveRoot/v1"
$LocalBase = $dotenv["BASE_URL"]
if (-not $LocalBase) { $LocalBase = "http://127.0.0.1:8788/v1" }  # Pages dev
if ($Base) { $RestBase = $Base.TrimEnd("/") } else { $RestBase = $Live }
$RtBase = if ($RealtimeBase) { $RealtimeBase.TrimEnd("/") } else { $RestBase }

# 3) Auth selection
function Get-AuthKey {
  param([string]$Mode,[hashtable]$DotEnv)
  if ($Mode -and $Mode -ne "dev") { return $Mode }
  $candidates = @(
    $env:OPENAI_CLIENT_KEY, $env:OPENAI_API_KEY, $env:OPENAI_KEY,
    $DotEnv["OPENAI_CLIENT_KEY"], $DotEnv["OPENAI_API_KEY"], $DotEnv["OPENAI_KEY"]
  ) | Where-Object { $_ -and $_.Trim() }
  if ($candidates.Count -eq 0) { throw "No OPENAI key found in env or .dev.vars" }
  return $candidates[0]
}
$Key = Get-AuthKey -Mode $Auth -DotEnv $dotenv
$Hdr = @{ "Authorization" = "Bearer $Key"; "Content-Type" = "application/json" }

# 4) Print summary
Write-Host "== Relay audit ==" -ForegroundColor Cyan
"LiveRoot : $LiveRoot"
"LiveBase : $Live"
"LocalBase: $LocalBase"
"RestBase : $RestBase"
"RtBase   : $RtBase"
"KeySrc   : $(
  if ($Auth -ne 'dev') {'(explicit)'}
  elseif ($env:OPENAI_CLIENT_KEY) {'env:OPENAI_CLIENT_KEY'}
  elseif ($env:OPENAI_API_KEY) {'env:OPENAI_API_KEY'}
  elseif ($env:OPENAI_KEY) {'env:OPENAI_KEY'}
  elseif ($dotenv["OPENAI_CLIENT_KEY"]) {'.dev.vars:OPENAI_CLIENT_KEY'}
  elseif ($dotenv["OPENAI_API_KEY"]) {'.dev.vars:OPENAI_API_KEY'}
  else {'.dev.vars:OPENAI_KEY'}
)"

# 5) Health
Write-Host "`n[*] Health (root)" -ForegroundColor Cyan
Invoke-RestMethod -Uri "$LiveRoot/health" -TimeoutSec $TimeoutSec | Out-Host

Write-Host "`n[*] Health (versioned)" -ForegroundColor Cyan
try {
  Invoke-RestMethod -Uri "$RestBase/health" -TimeoutSec $TimeoutSec | Out-Host
} catch {
  Write-Warning "/v1/health not implemented (ok if you didn’t add functions/v1/health.ts yet)."
}

# 6) Models
Write-Host "`n[*] /v1/models" -ForegroundColor Cyan
$models = Invoke-RestMethod -Method GET -Uri "$RestBase/models" -Headers $Hdr -TimeoutSec $TimeoutSec
"models count: $($models.data.Count)"

# 7) Chat ping
Write-Host "`n[*] /v1/chat/completions" -ForegroundColor Cyan
$body = @{ model = $ModelChat; messages = @(@{role="user";content="Say 'pong'."}); max_tokens = 5 } | ConvertTo-Json -Depth 6
$resp = Invoke-RestMethod -Method POST -Uri "$RestBase/chat/completions" -Headers $Hdr -Body $body -TimeoutSec $TimeoutSec
$txt  = $resp.choices[0].message.content
"reply: $txt"
if ($txt -match 'pong') { Write-Host "[PASS] chat pong" -ForegroundColor Green } else { Write-Warning "[WARN] chat did not echo 'pong'" }

# 8) Optional: realtime 101 probe (if RtBase provided)
if ($RealtimeBase) {
  Write-Host "`n[*] Realtime WS 101" -ForegroundColor Cyan
  $root = $RtBase -replace "/v1/?$",""
  $rt   = "$root/realtime?model=gpt-4o-realtime-preview-2024-12-17"
  $keyB64 = [Convert]::ToBase64String((1..16 | % {Get-Random -Max 256}))
  $hdrOpt = "-H `"Authorization: Bearer $Key`""
  $code = cmd /c "curl.exe --http1.1 -s -o NUL -w ""%{{http_code}}"" -H ""Connection: Upgrade"" -H ""Upgrade: websocket"" -H ""Sec-WebSocket-Version: 13"" -H ""Sec-WebSocket-Key: $keyB64"" $hdrOpt ""$rt"""
  if ($code -eq "101") { Write-Host "[PASS] Realtime 101 OK" -ForegroundColor Green } else { Write-Warning "[WARN] Realtime not upgrading (code $code)" }
}

Write-Host "`n== Done ==" -ForegroundColor Cyan
