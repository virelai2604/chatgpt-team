param(
  [string]$RepoCache = "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\tools\_cache\openai-node",
  [string]$Base = "https://chatgpt-team.pages.dev/v1"
)
$ErrorActionPreference='Stop'
if(Test-Path $RepoCache){ git -C "$RepoCache" pull --ff-only | Out-Null } else {
  New-Item -ItemType Directory -Force -Path (Split-Path $RepoCache) | Out-Null
  git clone https://github.com/openai/openai-node "$RepoCache" | Out-Null
}
# enumerate resource files (sdk endpoints are generated per resource)
$resourceDir = Join-Path $RepoCache "src\resources"
$resources = Get-ChildItem -LiteralPath $resourceDir -Recurse -File -Include *.ts | Select-Object -ExpandProperty BaseName | Sort-Object -Unique
# your relay endpoints we expect
$relay = @(
  "models","responses","chat/completions","completions","embeddings","images/generations",
  "audio/speech","audio/transcriptions","audio/translations","files","vector-stores","assistants","threads","runs"
)
# naive map: mark present if resource name contains the segment
$result = foreach($r in $relay){
  $hit=$resources | Where-Object { $_ -like "*$((($r -replace '/','-')).ToLower())*" }
  [pscustomobject]@{ relay_endpoint=$r; sdk_resource_match=($hit -join ','); present=[bool]$hit }
}
# print table
$result | Sort-Object present, relay_endpoint | Format-Table -AutoSize
# emit a concise "missing" list
"--- Missing in relay vs SDK resources (heuristic) ---"
$result | Where-Object { -not $_.present } | Select-Object -ExpandProperty relay_endpoint
