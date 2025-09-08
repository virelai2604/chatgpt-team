#!/usr/bin/env bash
# End-to-end smoke test for an OpenAI-compatible relay.
# Usage:
#   chmod +x ./smoke.sh
#   BASE="https://chatgpt-team.pages.dev" OPENAI_API_KEY="sk-..." ./smoke.sh
set -euo pipefail

BASE="${BASE:-http://localhost:8787}"
KEY="${OPENAI_API_KEY:-}"
REQUIRED_TOOLS=("curl" "jq")
for t in "${REQUIRED_TOOLS[@]}"; do
  command -v "$t" >/dev/null 2>&1 || { echo "[FATAL] Missing $t"; exit 2; }
done

if [[ -z "$KEY" ]]; then
  echo "[FATAL] Set OPENAI_API_KEY"; exit 2
fi

BASE="${BASE%/}"
HDR=(-H "Authorization: Bearer $KEY" -H "Content-Type: application/json")
DL="./downloads"
mkdir -p "$DL"

failures=()

pass() { echo -e "\033[32m[PASS]\033[0m $1"; }
fail() { echo -e "\033[31m[FAIL]\033[0m $1 -> $2"; failures+=("$1: $2"); }

# 1) Models
if out=$(curl -sS "$BASE/v1/models" -H "Authorization: Bearer $KEY"); then
  if echo "$out" | jq -e '.data' >/dev/null; then pass "GET /v1/models"; else fail "GET /v1/models" "no data[]"; fi
else fail "GET /v1/models" "HTTP error"; fi

CHAT_MODEL="gpt-4o-mini"
EMBED_MODEL="text-embedding-3-small"
TTS_MODEL="gpt-4o-mini-tts"

# 2) Chat
body=$(jq -n --arg m "$CHAT_MODEL" '{model:$m,messages:[{role:"system",content:"You are helpful."},{role:"user",content:"Say '\''pong'\''."}],temperature:0}')
if out=$(curl -sS "$BASE/v1/chat/completions" "${HDR[@]}" -d "$body"); then
  if echo "$out" | jq -e '.choices[0].message.content | test("pong"; "i")' >/dev/null; then pass "POST /v1/chat/completions"; else fail "POST /v1/chat/completions" "unexpected reply: $(echo "$out" | jq -r '.choices[0].message.content // empty')"; fi
else fail "POST /v1/chat/completions" "HTTP error"; fi

# 3) Embeddings
body=$(jq -n --arg m "$EMBED_MODEL" '{model:$m,input:["hello world"]}')
if out=$(curl -sS "$BASE/v1/embeddings" "${HDR[@]}" -d "$body"); then
  if echo "$out" | jq -e '.data[0].embedding' >/dev/null; then pass "POST /v1/embeddings"; else fail "POST /v1/embeddings" "no embedding"; fi
else fail "POST /v1/embeddings" "HTTP error"; fi

# 4) Images (optional)
if [[ "${SMOKE_SKIP_OPTIONAL:-0}" != "1" ]]; then
  body=$(jq -n '{model:"gpt-image-1",prompt:"simple black square icon",size:"256x256",response_format:"b64_json"}')
  if out=$(curl -sS "$BASE/v1/images/generations" "${HDR[@]}" -d "$body"); then
    b64=$(echo "$out" | jq -r '.data[0].b64_json // empty')
    if [[ -n "$b64" ]]; then
      echo "$b64" | base64 -d > "$DL/smoke-image.png"
      pass "POST /v1/images/generations"
    else fail "POST /v1/images/generations" "no b64_json"; fi
  else fail "POST /v1/images/generations" "HTTP error"; fi

  # 5) TTS
  body=$(jq -n --arg m "$TTS_MODEL" '{model:$m,input:"Hello from the relay smoke test.",voice:"alloy",format:"mp3"}')
  if curl -sS "$BASE/v1/audio/speech" "${HDR[@]}" -d "$body" -o "$DL/smoke-tts.mp3"; then
    if [[ -s "$DL/smoke-tts.mp3" ]]; then pass "POST /v1/audio/speech"; else fail "POST /v1/audio/speech" "empty file"; fi
  else fail "POST /v1/audio/speech" "HTTP error"; fi

  # 6) STT — send a tiny WAV (expect 200/400 depending on relay capabilities)
  : > "$DL/beep.wav"
  # (Keep it empty or pre-created; some relays allow empty audio for health checks.)
  if out=$(curl -sS "$BASE/v1/audio/transcriptions" -H "Authorization: Bearer $KEY" \
      -F "model=whisper-1" -F "file=@$DL/beep.wav" 2>/dev/null); then
    pass "POST /v1/audio/transcriptions"
  else
    # Non-fatal: mark as failed but continue
    fail "POST /v1/audio/transcriptions" "error (relay may not support STT)"
  fi

  # 7) Files API
  echo '{"text":"hello"}' > "$DL/tiny.jsonl"
  if out=$(curl -sS "$BASE/v1/files" -H "Authorization: Bearer $KEY" -F "purpose=assistants" -F "file=@$DL/tiny.jsonl"); then
    fid=$(echo "$out" | jq -r '.id // empty')
    if [[ -n "$fid" ]]; then
      pass "POST /v1/files (upload)"
      if curl -sS "$BASE/v1/files" -H "Authorization: Bearer $KEY" | jq -e '.data' >/dev/null; then pass "GET /v1/files (list)"; else fail "GET /v1/files (list)" "no data"; fi
      if curl -sS "$BASE/v1/files/$fid/content" -H "Authorization: Bearer $KEY" -o "$DL/downloaded.jsonl"; then
        [[ -s "$DL/downloaded.jsonl" ]] && pass "GET /v1/files/{id}/content" || fail "GET /v1/files/{id}/content" "empty"
      else fail "GET /v1/files/{id}/content" "HTTP error"; fi
      if curl -sS -X DELETE "$BASE/v1/files/$fid" -H "Authorization: Bearer $KEY" | jq -e '.deleted == true' >/dev/null; then
        pass "DELETE /v1/files/{id}"
      else fail "DELETE /v1/files/{id}" "delete=false"; fi
    else fail "POST /v1/files (upload)" "no id"; fi
  else fail "POST /v1/files (upload)" "HTTP error"; fi
fi

if (( ${#failures[@]} )); then
  echo
  echo "One or more checks failed:"
  for f in "${failures[@]}"; do echo " - $f"; done
  exit 1
else
  echo
  echo "All required checks passed."
fi
