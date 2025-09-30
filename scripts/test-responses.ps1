$env:OPENAI_API_KEY = "sk-xxx"
$env:OPENAI_ORG_ID = "org-xxx"
$base = "http://localhost:8788/v1"
$body = @{
  model = "gpt-4"
  input = @(@{role="user"; content="ping"})
} | ConvertTo-Json -Depth 4

Invoke-RestMethod "$base/responses" -Method POST -Headers @{
  "Authorization" = "Bearer $env:OPENAI_API_KEY"
  "OpenAI-Organization" = $env:OPENAI_ORG_ID
  "Content-Type" = "application/json"
} -Body $body
