Set-Location -LiteralPath "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team"
$out = "$env:USERPROFILE\Desktop\test-assistants.txt"
$base = "https://chatgpt-team.pages.dev/v1"
$headers = @{
  Authorization = "Bearer $env:OPENAI_API_KEY"
  "OpenAI-Org" = "org-BE0YNlrYbCShFGQxMkW2f0fU"
  "OpenAI-Project" = "proj_sZ0J3FtvBLrNJic6pXlx56Mm"
}

$t = Invoke-RestMethod "$base/threads" -Method POST -Headers $headers -ContentType "application/json"
$tid = $t.id

$body = @{ role = "user"; content = "What's 9 x 6?" } | ConvertTo-Json
Invoke-RestMethod "$base/threads/$tid/messages" -Headers $headers -Method POST -Body $body -ContentType "application/json" | Out-Null

$r = Invoke-RestMethod "$base/threads/$tid/runs" -Headers $headers -Method POST -Body '{"assistant_id":"asst_abc"}' -ContentType "application/json"
"Run ID = $($r.id)" | Out-File -Encoding UTF8 $out
