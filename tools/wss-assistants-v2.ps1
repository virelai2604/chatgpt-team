param(
  [string]$WS    = "wss://chatgpt-team-realtime.virelai.workers.dev/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
  [string]$Proto = "oai-realtime"   # or "oai-realtime-broker"
)
$ErrorActionPreference='Stop'
if(-not $env:OPENAI_API_KEY){ $env:OPENAI_API_KEY = Read-Host "OpenAI API key (session only)" }

$auth  = "Authorization: Bearer $($env:OPENAI_API_KEY)"
$beta  = "OpenAI-Beta: realtime=v1"
$tip = @"
TIP: After connect, send:
{"type":"response.create","response":{"instructions":"Say hello from realtime."}}
"@
Write-Host $tip

if (Get-Command websocat -ErrorAction SilentlyContinue) {
  # websocat supports --protocol for subprotocols
  websocat --protocol $Proto -H "$auth" -H "$beta" $WS
} else {
  if (-not (Get-Command npx -ErrorAction SilentlyContinue)) { throw "Neither websocat nor npx found. Install one: choco install websocat OR Node.js LTS." }
  # wscat uses --protocol (or -s); headers alone are NOT enough
  npx wscat@8 -c $WS --protocol $Proto -H "$auth" -H "$beta"
}
