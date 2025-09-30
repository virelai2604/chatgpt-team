$env:OPENAI_API_KEY = "sk-xxx"
$env:OPENAI_ORG_ID = "org-xxx"
$base = "http://localhost:8788/v1/files"
$localFile = ".\sample.json"

curl -X POST $base `
  -H "Authorization: Bearer $env:OPENAI_API_KEY" `
  -H "OpenAI-Organization: $env:OPENAI_ORG_ID" `
  -F "file=@$localFile" `
  -F "purpose=assistants" `
  --fail
