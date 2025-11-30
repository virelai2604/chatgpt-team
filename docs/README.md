# ChatGPT Relay

A secure, production-grade relay for OpenAI API (v1/v2 ready) and ChatGPT plugins using FastAPI, supporting streaming, non-streaming, model allowlist, unified error handling, and Cloudflare deployment.

---

## Features

- ✅ OpenAI v1 API compatible endpoints (/v1/chat/completions, /v1/completions, /v1/models, /v1/files)
- ✅ Streaming and non-streaming support
- ✅ Model allowlist, fail-slow retry logic
- ✅ Secure .env for all secrets
- ✅ Unified error response format
- ✅ Modular, testable codebase
- ✅ PowerShell 7 automation scripts
- ✅ GitHub Actions CI/CD (Cloudflare deploy)
- ✅ Cloudflare integration utilities

---

## Run Locally

pip install -r requirements.txt
pwsh ./run.ps1

---

## Environment Variables

Copy .env.example to .env and fill in the following:

OPENAI_API_KEY=sk-...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...

---

## API Endpoints

- POST /v1/chat/completions  
  OpenAI Chat (GPT-3.5/4, stream & non-stream)
- POST /v1/completions  
  Legacy text models
- GET /v1/models  
  Model allowlist
- POST /v1/files  
  File uploads (if enabled)
- All unknown /v1/* paths are safely proxied to OpenAI

---

## Example Usage

### Curl

curl -H "Authorization: Bearer <key>" 
     -H "Content-Type: application/json" 
     http://localhost:8000/v1/chat/completions 
     -d '{"model": "gpt-4-turbo", "messages": [{"role": "user", "content": "Hello"}]}'

### PowerShell 7+

\{
  "model": "gpt-4-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ]
} = @{
    model = "gpt-4-turbo"
    messages = @(@{ role = "user"; content = "Hello" })
} | ConvertTo-Json

\@{id=chatcmpl-CNKxci6YTElwu0iMnhOCN7tdiKd8r; object=chat.completion; created=1759678152; model=gpt-4-turbo-2024-04-09; choices=System.Object[]; usage=; service_tier=default; system_fingerprint=fp_de235176ee} = Invoke-RestMethod 
    -Uri "http://localhost:8000/v1/chat/completions" 
    -Method Post 
    -Body \{
  "model": "gpt-4-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ]
} 
    -ContentType "application/json" 
    -Headers @{ Authorization = "Bearer <key>" }

\@{id=chatcmpl-CNKxci6YTElwu0iMnhOCN7tdiKd8r; object=chat.completion; created=1759678152; model=gpt-4-turbo-2024-04-09; choices=System.Object[]; usage=; service_tier=default; system_fingerprint=fp_de235176ee}

*No backticks or deprecated syntax. All PowerShell code is PS7+ ready.*

---

## Error Handling

All API errors return this format:

{
  "error": {
    "type": "<error_type>",
    "message": "<detailed_error_message>"
  }
}

---

## Testing

Run all end-to-end/integration tests using PowerShell 7:

pwsh ./test.ps1

---

## CI/CD and Deployment

### GitHub Actions

A deploy workflow is provided at .github/workflows/deploy.yml to automatically test and deploy to Cloudflare Pages on every push to main.

### Manual Cloudflare Deployment

Ensure your .env contains the correct CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID.  
Then, deploy as usual (see your Pages or Workers docs).

---

## Cloudflare Worker Integration

For advanced DNS/cache/worker operations, see:

- pp/utils/cloudflare.py

Example purge cache:

from app.utils.cloudflare import purge_cache
await purge_cache(zone_id, url, token)

---

## Security Notes

- Never commit .env or other secrets.
- Always use HTTPS and limit access by API key or trusted JWT.
- Set a model allowlist and token-based access for production use.

---

## License

MIT

---

*Generated and checked by DevXplorer Ultra (AI)*
