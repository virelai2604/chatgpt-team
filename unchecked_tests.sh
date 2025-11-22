#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
AUTH_HEADER="Authorization: Bearer ${RELAY_KEY:-dummy}"

echo "Using BASE_URL=${BASE_URL}"
echo "Using RELAY_KEY=${RELAY_KEY:-dummy}"
echo

# 0) BASIC HEALTH CHECK
echo "=== 0) HEALTH CHECK ==="

echo "--- GET /v1/health"
curl -sS "${BASE_URL}/v1/health" \
  -H "${AUTH_HEADER}" \
  | jq '.'

echo
# 1) TOOLS MANIFEST TESTS
echo "=== 1) TOOLS MANIFEST TESTS ==="

echo "--- GET /v1/tools"
curl -sS "${BASE_URL}/v1/tools" \
  -H "${AUTH_HEADER}" \
  | jq '.'

echo
echo "--- GET /v1/tools/video_generation"
curl -sS "${BASE_URL}/v1/tools/video_generation" \
  -H "${AUTH_HEADER}" \
  | jq '.'

echo
echo "--- GET /v1/tools/realtime_session"
curl -sS "${BASE_URL}/v1/tools/realtime_session" \
  -H "${AUTH_HEADER}" \
  | jq '.'

echo
echo "=== 2) AGENTIC /v1/responses TEST ==="

cat > /tmp/agentic_payload.json << 'EOAGENT'
{
  "model": "gpt-4.1-mini",
  "input": "You are an assistant behind a relay. Think step by step, and then reply with the exact text: agentic-ok. You may use tools if helpful.",
  "tool_choice": "auto",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "web_search",
        "description": "Search the web for information.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string" }
          },
          "required": ["query"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "video_generation",
        "description": "Generate a short video clip using the relay video API.",
        "parameters": {
          "type": "object",
          "properties": {
            "prompt": { "type": "string" },
            "duration_seconds": { "type": "integer" }
          },
          "required": ["prompt"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "realtime_session",
        "description": "Request a realtime session descriptor.",
        "parameters": {
          "type": "object",
          "properties": {
            "model": { "type": "string" }
          },
          "required": []
        }
      }
    }
  ]
}
EOAGENT

echo "--- POST /v1/responses (agentic with tools)"
curl -sS "${BASE_URL}/v1/responses" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d @/tmp/agentic_payload.json \
  | jq '.'

echo
echo "=== 3) VIDEOS TESTS ==="

cat > /tmp/video_payload.json << 'EOVID'
{
  "model": "gpt-4o-mini",
  "input": "A short abstract animation that spells relay-video-ok."
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
  echo "No video id returned (this may happen if upstream returns a job or error)."
fi

echo
echo "=== 4) REALTIME SESSION TEST ==="

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
  | jq '.'

echo
echo "=== DONE: Unchecked relay surfaces tested ==="
