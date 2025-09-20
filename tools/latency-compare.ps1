param(
  [string]$Base = "https://chatgpt-team.pages.dev/v1",
  [int]$N = 5
)
$ErrorActionPreference='Stop'
if(-not $env:OPENAI_API_KEY){ throw "OPENAI_API_KEY not set" }
$H=@{ Authorization="Bearer $($env:OPENAI_API_KEY)"; 'Content-Type'='application/json' }

function Measure([string]$name,[string]$uri,[string]$json){
  $times=@()
  for($i=0;$i -lt $N;$i++){
    $sw=[Diagnostics.Stopwatch]::StartNew()
    Invoke-RestMethod -Uri $uri -Method POST -Headers $H -Body $json -TimeoutSec 60 | Out-Null
    $sw.Stop(); $times += $sw.Elapsed.TotalMilliseconds
  }
  [PSCustomObject]@{ Name=$name; Median=[Math]::Round(($times | Sort-Object)[[int]($times.Count/2)],1); Samples=$times -join "," }
}

$chat = @{ model="gpt-4o-mini"; messages=@(@{role="user"; content="ok"}); max_tokens=8 } | ConvertTo-Json -Depth 6
$r1 = Measure "chat/completions" "$Base/chat/completions" $chat
$r2 = Measure "responses" "$Base/responses" (@{ model="gpt-5-mini"; input="ok"; max_output_tokens=8 }|ConvertTo-Json)

# 2× threshold report
function Rpt($r){ "$($r.Name): median=${($r.Median)} ms | threshold(2x)=$([math]::Round($r.Median*2,1)) ms" }
Rpt $r1; Rpt $r2
