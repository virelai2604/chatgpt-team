# PowerShell 7 – curl test for /v1/files (no project header)
$env:OPENAI_API_KEY = "sk-proj-xxx"
$env:OPENAI_ORG_ID = "org-xxx"
$base = "http://localhost:8788/v1/files"
$localFile = ".\sample.json"

& curl -X POST $base `
  -H "Authorization: Bearer $env:OPENAI_API_KEY" `
  -H "OpenAI-Organization: $env:OPENAI_ORG_ID" `
  -F "file=@$localFile" `
  -F "purpose=assistants" `
  --fail --retry 2
