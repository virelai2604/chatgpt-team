Set-Location -LiteralPath "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team"
openapi-generator-cli generate `
  -g typescript-axios `
  -i openai_relay_schema.yaml `
  -o tools/sdk-typescript `
  --skip-validate-spec `
  --additional-properties supportsES6=true
