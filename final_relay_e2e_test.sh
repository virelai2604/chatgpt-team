#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
AUTH_HEADER="Authorization: Bearer ${RELAY_KEY:-dummy}"

echo "Using BASE_URL=${BASE_URL}"
echo "Using RELAY_KEY=${RELAY_KEY:-dummy}"
echo

########################################
# 0) HEALTH
########################################
echo "=== 0) HEALTH CHECK ==="
echo "--- GET /v1/health"
curl -sS "${BASE_URL}/v1/health" \
  -H "${AUTH_HEADER}" \
  | jq '.'
echo

########################################
# 1) MODELS – AVAILABILITY
########################################
echo "=== 1) MODELS LIST ==="
echo "--- GET /v1/models"
MODELS_JSON="$(curl -sS "${BASE_URL}/v1/models" -H "${AUTH_HEADER}")"

echo "${MODELS_JSON}" | jq '{object, total: (.data | length)}'
echo
echo "--- Some relevant models (ids) ---"
echo "${MODELS_JSON}" | jq -r '.data[].id' | grep -E 'gpt-4\.1|gpt-4o|gpt-4o-mini|gpt-image-1|sora-2|sora-2-pro' || true
echo

########################################
# 2) TOOLS MANIFEST
########################################
echo "=== 2) TOOLS MANIFEST ==="
echo "--- GET /v1/tools"
TOOLS_JSON="$(curl -sS "${BASE_URL}/v1/tools" -H "${AUTH_HEADER}")"
echo "${TOOLS_JSON}" | jq '{object, tool_count: (.data | length), tools: [.data[].name]}'
echo

########################################
# 3) IMAGE GENERATION (TOP-LEVEL)
########################################
echo "=== 3) IMAGE GENERATION TEST (/v1/images/generations) ==="

cat > /tmp/image_payload.json << 'EOIMG'
{
  "model": "gpt-image-1",
  "prompt": "A simple icon that says relay-image-ok.",
  "size": "1024x1024"
}
EOIMG

echo "--- POST /v1/images/generations"
curl -sS "${BASE_URL}/v1/images/generations" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d @/tmp/image_payload.json \
  | jq '{
      object,
      created,
      data_count: ( .data | length ),
      first_item: ( .data[0] // null )
  }'
echo

########################################
# 4) VIDEO GENERATION (TOP-LEVEL, SORA-2)
########################################
echo "=== 4) VIDEO GENERATION TEST (/v1/videos) ==="

cat > /tmp/video_payload.json << 'EOVID'
{
  "model": "sora-2",
  "prompt": "A short abstract animation that spells relay-video-ok."
}
EOVID

echo "--- POST /v1/videos"
VIDEO_RESPONSE="$(curl -sS "${BASE_URL}/v1/videos" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d @/tmp/video_payload.json)"

echo "${VIDEO_RESPONSE}" | jq '.'

VIDEO_ID="$(echo "${VIDEO_RESPONSE}" | jq -r '.id // .data[0].id // empty')"

if [ -n "${VIDEO_ID}" ] && [ "${VIDEO_ID}" != "null" ]; then
  echo
  echo "--- GET /v1/videos/${VIDEO_ID}"
  curl -sS "${BASE_URL}/v1/videos/${VIDEO_ID}" \
    -H "${AUTH_HEADER}" \
    | jq '.'
else
  echo
  echo "No video id returned (this may happen if upstream returns an async job handle or another non-id object)."
fi
echo

########################################
# 5) RESPONSES – BASIC TEXT
########################################
echo "=== 5) RESPONSES BASIC TEXT TEST ==="

cat > /tmp/responses_basic.json << 'EOBASIC'
{
  "model": "gpt-4.1-mini",
  "input": [
    {
      "role": "user",
      "content": "Say: relay-http-ok"
    }
  ]
}
EOBASIC

echo "--- POST /v1/responses (basic)"
curl -sS "${BASE_URL}/v1/responses" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d @/tmp/responses_basic.json \
  | jq '{
      id,
      status,
      model,
      first_output_text: ( .output[0].content[0].text // null ),
      error
  }'
echo

########################################
# 6) MANIFEST-WIDE TOOL SWEEP (ALL TOOLS)
########################################
echo "=== 6) MANIFEST-WIDE TOOL SWEEP VIA /v1/responses ==="
echo "Using each tool name from /v1/tools as a function tool in Responses v1."

TOOL_NAMES=$(echo "${TOOLS_JSON}" | jq -r '.data[].name')

for TOOL in ${TOOL_NAMES}; do
  echo
  echo ">>> Testing tool via Responses API: ${TOOL}"

  cat > /tmp/tool_test_payload.json <<EOF
{
  "model": "gpt-4.1-mini",
  "input": [
    {
      "role": "user",
      "content": "You are behind a relay. We are testing tool: ${TOOL}. Reply with the exact text: tool-${TOOL}-ok."
    }
  ],
  "tool_choice": "auto",
  "tools": [
    {
      "type": "function",
      "name": "${TOOL}",
      "description": "Stub definition for ${TOOL} during manifest testing.",
      "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": true
      }
    }
  ]
}
EOF

  RESPONSE="$(curl -sS "${BASE_URL}/v1/responses" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -d @/tmp/tool_test_payload.json)"

  echo "${RESPONSE}" | jq '{
    id,
    status,
    model,
    first_output_text: ( .output[0].content[0].text // null ),
    error
  }'
done
echo

########################################
# 7) REALTIME SESSION
########################################
echo "=== 7) REALTIME SESSION TEST ==="

cat > /tmp/realtime_payload.json << 'EOREAL'
{
  "model": "gpt-4o-realtime-preview-2024-10-01",
  "instructions": "You are a realtime test assistant behind a relay."
}
EOREAL

echo "--- POST /v1/realtime/sessions"
curl -sS "${BASE_URL}/v1/realtime/sessions" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: realtime=v1" \
  -d @/tmp/realtime_payload.json \
  | jq '{
      object,
      id,
      model,
      modalities,
      instructions,
      client_secret: (.client_secret.value // null),
      expires_at
  }'
echo

echo "=== DONE: FINAL RELAY E2E TEST (HEALTH + MODELS + IMAGES + VIDEOS + RESPONSES + ALL TOOLS + REALTIME) ==="
