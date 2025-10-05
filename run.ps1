# Ensure you're in the project root
Set-Location -LiteralPath "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team"

# Activate venv
.\.venv\Scripts\Activate.ps1

# Run the relay API
uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
