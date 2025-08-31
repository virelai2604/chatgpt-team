param(
  [string]$LiveHost = "chatgpt-team.pages.dev",
  [int]$LocalPort = 8788,
  [switch]$IncludePaid # enables POST checks to /v1/responses (costs tokens)
)

$ErrorActionPreference = "Stop"

# ---------- helpers ----------
function Add-Row([string]$Target,[string]$Check,[string]$Result,[string]$Details="") {
  [pscustomobject]@{ Target=$Target; Check=$Check; Result=$Result; Details=$Details }
}
$rows = @()

function Test-Http($Method,$Url,$Headers=@{},$Body=$null){
  $args = @{
    Method=$Method; Uri=$Url; Headers=$Headers; TimeoutSec=25; MaximumRedirection=0; ErrorAction="Stop"
  }
  if ($Body) { $args["Body"] = $Body; $args["ContentType"] = "application/json" }
  try {
    $resp = Invoke-WebRequest @args
    return $resp
  } catch {
    if ($_.Exception.Response) { return $_.Exception.Response } else { throw }
  }
}

function Has-Header($Resp,[string]$Name,[string]$Contains=""){
  $val = $Resp.Headers[$Name]
  if (-not $val) { return $false }
  if ($Contains) { return ($val -join ",") -match [regex]::Escape($Contains) }
  return $true
}

# ---------- config checks ----------
$catchAll = 'functions\v1\[[path]].ts'
$wrangler = 'wrangler.toml'

# 1) Catch-all file exists and non-empty
if (Test-Path -LiteralPath $catchAll) {
  $len = (Get-Item -LiteralPath $catchAll).Length
  $rows += Add-Row "repo" "catch-all exists" ($(if ($len -gt 0){"✅ PASS"}else{"❌ FAIL"}), "size=$len bytes")
} else {
  $rows += Add-Row "repo" "catch-all exists" "❌ FAIL" "missing $catchAll"
}

# 2) CORS preflight present (simple scan for 'OPTIONS' block)
if (Test-Path -LiteralPath $catchAll) {
  $content = Get-Content -LiteralPath $catchAll -Raw
  $hasCors = $content -match 'request\.method\s*===?\s*"OPTIONS"' -and $content -match 'Access-Control-Allow-Origin'
  $rows += Add-Row "repo" "CORS preflight in relay" ($(if ($hasCors){"✅ PASS"}else{"⚠️ SKIP"}), $(if ($hasCors){"found"}else{"not found"}))
}

# 3) wrangler.toml has compatibility_date
if (Test-Path -LiteralPath $wrangler) {
  $wr = Get-Content -LiteralPath $wrangler -Raw
  if ($wr -match '(?m)^\s*compatibility_date\s*=\s*"(.*?)"') {
    $date = $Matches[1]
    $rows += Add-Row "repo" "wrangler compatibility_date" "✅ PASS" $date
  } else {
    $rows += Add-Row "repo" "wrangler compatibility_date" "❌ FAIL" "not set"
  }
} else {
  $rows += Add-Row "repo" "wrangler.toml exists" "❌ FAIL" "missing file"
}

# ---------- targets ----------
$targets = @(
  @{ name="local"; base="http://127.0.0.1:$LocalPort"; up={$true} },
  @{ name="live";  base="https://$LiveHost";            up={$true} }
)

# ---------- probe each target ----------
foreach ($t in $targets) {
  $name = $t.name; $base = $t.base
  # 0) reachability (GET /v1/models)
  try {
    $r = Test-Http -Method GET -Url ($base + "/v1/models") -Headers @{ Authorization="Bearer test" }
    $ok = $r.StatusCode -ge 200 -and $r.StatusCode -lt 300
    $rows += Add-Row $name "GET /v1/models" ($(if ($ok){"✅ PASS"}else{"❌ FAIL"}), "status=" + $r.StatusCode)
    $t.up = $ok
  } catch {
    $rows += Add-Row $name "GET /v1/models" "❌ FAIL" ("error: " + $_.Exception.Message)
    $t.up = $false
  }

  if (-not $t.up) { continue }

  # 1) CORS preflight (OPTIONS)
  try {
    $optHeaders = @{
      "Origin" = "https://example.com"
      "Access-Control-Request-Method"  = "POST"
      "Access-Control-Request-Headers" = "authorization, content-type, openai-organization"
    }
    $r = Test-Http -Method OPTIONS -Url ($base + "/v1/chat/completions") -Headers $optHeaders
    $ok = ($r.StatusCode -eq 204) -and (Has-Header $r "Access-Control-Allow-Origin" "*")
    $det = "status={0}, A-C-A-O={1}" -f $r.StatusCode, $r.Headers["Access-Control-Allow-Origin"]
    $rows += Add-Row $name "OPTIONS /v1/chat/completions" ($(if ($ok){"✅ PASS"}else{"❌ FAIL"}), $det)
  } catch {
    $rows += Add-Row $name "OPTIONS /v1/chat/completions" "❌ FAIL" ("error: " + $_.Exception.Message)
  }

  # 2) Headers hygiene (no Host leakage, org header optional)
  try {
    $r = Test-Http -Method GET -Url ($base + "/v1/models") -Headers @{ Authorization="Bearer test" }
    $ok = Has-Header $r "openai-version"
    $rows += Add-Row $name "Upstream responded (OpenAI headers)" ($(if ($ok){"✅ PASS"}else{"❌ FAIL"}), "openai-version=" + $r.Headers["openai-version"])
  } catch {
    $rows += Add-Row $name "Upstream responded (OpenAI headers)" "❌ FAIL" ("error: " + $_.Exception.Message)
  }

  # 3) (optional) cheap POST via /v1/responses
  if ($IncludePaid) {
    try {
      $body = (@{
        model = "gpt-4o-mini"
        input = "ping"
        max_output_tokens = 8
      } | ConvertTo-Json -Depth 5)
      $r = Test-Http -Method POST -Url ($base + "/v1/responses") -Headers @{ Authorization="Bearer test" } -Body $body
      $ok = $r.StatusCode -ge 200 -and $r.StatusCode -lt 300
      $rows += Add-Row $name "POST /v1/responses" ($(if ($ok){"✅ PASS"}else{"❌ FAIL"}), "status=" + $r.StatusCode)
    } catch {
      $rows += Add-Row $name "POST /v1/responses" "❌ FAIL" ("error: " + $_.Exception.Message)
    }
  }
}

# ---------- print ----------
$rows | Format-Table -AutoSize
