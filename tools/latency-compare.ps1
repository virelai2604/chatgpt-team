param(
  [string]$Base = "https://chatgpt-team.pages.dev/v1",
  [int]$ClientDelayMs = 300           # artificial client delay to simulate ~2× latency
)
$ErrorActionPreference='Stop'
function Time([scriptblock]$sb){ $sw=[Diagnostics.Stopwatch]::StartNew(); & $sb; $sw.Stop(); return $sw.Elapsed.TotalMilliseconds }
if(-not $env:OPENAI_API_KEY){ $env:OPENAI_API_KEY = Read-Host "OpenAI API key (session only)" }
$H=@{ Authorization="Bearer $($env:OPENAI_API_KEY)"; 'Content-Type'='application/json' }
$endpoints=@(
  @{ name="chat/completions";   uri="$Base/chat/completions"; body=(@{model="gpt-4o-mini";messages=@(@{role="user";content="ping"})}|ConvertTo-Json -Depth 6) },
  @{ name="responses";          uri="$Base/responses";        body=(@{model="gpt-5-mini";input="ping"}|ConvertTo-Json -Depth 6) },
  @{ name="embeddings";         uri="$Base/embeddings";       body=(@{model="text-embedding-3-small";input="hi"}|ConvertTo-Json -Depth 6) },
  @{ name="images/generations"; uri="$Base/images/generations";body=(@{model="gpt-image-1";prompt="dot"}|ConvertTo-Json -Depth 6) }
)
function Call($e){ Invoke-RestMethod -Uri $e.uri -Method POST -Headers $H -Body $e.body -TimeoutSec 60 | Out-Null }
$rows=@()
foreach($e in $endpoints){
  $t1=Time{ Call $e }
  Start-Sleep -Milliseconds $ClientDelayMs  # artificial delay to approximate 2× user-perceived roundtrip
  $t2=Time{ Call $e }
  $rows += [pscustomobject]@{ endpoint=$e.name; run1_ms=[math]::Round($t1,1); run2_ms=[math]::Round($t2,1); fold=[math]::Round(($t2/$t1),2) }
}
$rows | Format-Table -AutoSize
