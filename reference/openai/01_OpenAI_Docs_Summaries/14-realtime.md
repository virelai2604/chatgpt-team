---
source_id: oa_docs_realtime
title: Realtime
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/guides/realtime
  - https://developers.openai.com/api/docs/guides/realtime-websocket
  - https://developers.openai.com/api/docs/guides/realtime-webrtc
  - https://github.com/openai/openai-openapi
  - https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml
  - https://openai.com/index/introducing-gpt-realtime/
  - https://github.com/openai/openai-cookbook
fetched: 2026-07-12
fetch_method: openapi.yaml fetched via raw.githubusercontent (81040 lines, grepped for realtime paths/objects/events); model name + transports web-searched (platform docs 403-blocked)
pull_status: web_verified
verify: curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -nE '/realtime|Realtime[A-Za-z]+:|session\.update|response\.create'
---

# Realtime

> Provenance: Spec-level facts (paths, schema objects, event names) come from the fetched openai-openapi `openapi.yaml`; the current model name and transport list are web-searched because `platform.openai.com/docs/guides/realtime` returns 403 to fetch.

## What it is
The Realtime API is OpenAI's low-latency, event-driven interface for **speech-to-speech** (and speech-to-text) interaction with a realtime model. Instead of a request/response REST call, the client opens a persistent connection, streams audio (and text) up, and receives streamed audio/text/transcript deltas back. It is aimed at production voice agents: barge-in/interruption handling, server-side VAD, function calling, and phone integration.

## Transports (WebSocket / WebRTC) & sessions
The spec + docs describe three transports; pick by where the audio originates:
- **WebRTC** — browser/client-side audio. The peer connection handles mic capture and playback; app/server events are exchanged over a WebRTC data channel. Auth uses a short-lived client secret (ephemeral token) rather than the raw API key. Spec: `POST /realtime/client_secrets` (`RealtimeCreateClientSecretRequest/Response`).
- **WebSocket** — server-to-server. You manually manage the input audio buffer, sending base64-encoded audio as JSON events and handling audio deltas yourself. This is the transport the relay in this repo proxies.
- **SIP / native telephony** — inbound phone calls; spec exposes `POST /realtime/calls`, plus `/realtime/calls/{call_id}/accept|hangup|refer|reject` and the `realtime.call.incoming` webhook.

Realtime-related **paths** confirmed in `openapi.yaml`:
`/realtime/calls`, `/realtime/calls/{call_id}/{accept,hangup,refer,reject}`, `/realtime/client_secrets`, `/realtime/sessions`, `/realtime/transcription_sessions`, `/realtime/translations/client_secrets`.

**Schema objects** (sample): `RealtimeSessionCreateRequest`, `RealtimeSessionCreateResponse`, `RealtimeSessionCreateRequestGA`, `RealtimeCallCreateRequest`, `RealtimeCreateClientSecretRequest/Response`, `RealtimeTranscriptionSessionCreateRequest`, `RealtimeAudioFormats`, `RealtimeConversationItem`, and a `RealtimeBetaClientEvent*` family. A **session** is created (or configured via `session.update`) with fields like `model`, modalities, voice, audio formats, turn_detection, tools, and instructions.

## Current model name (verified 2026-07-12)
- The stable/GA model **alias is `gpt-realtime`** — this is what the openapi examples use (`"model":"gpt-realtime"`) and what this repo defaults to.
- As of **July 2026 the newest realtime models are `gpt-realtime-2.1` and `gpt-realtime-2.1-mini`** (announced ~2026-07-06, ~25% P95 latency reduction). The older `gpt-4o-realtime-preview` line still exists but is superseded; `gpt-realtime`/`gpt-realtime-mini` (dated snapshots `gpt-realtime-2025-08-28`, `gpt-realtime-mini-2025-10-06`, etc.) remain valid.
- Net: use `gpt-realtime` as the safe current alias; `gpt-realtime-2.1` is the latest capability tier. NOT `gpt-4o-realtime-preview` anymore.

## Key events (session.update, input_audio_buffer, response.create, etc.)
Confirmed present as event-type strings in `openapi.yaml`. Client→server and server→client events include:
- **Session:** `session.update` (client sets/updates config), `session.created` (server ack).
- **Input audio buffer (WS):** `input_audio_buffer.append`, `input_audio_buffer.commit`, `input_audio_buffer.clear`.
- **Conversation:** `conversation.item.create` (inject a text/audio/function-output item).
- **Response:** `response.create` (request a model turn), `response.done` (turn complete), streamed deltas `response.output_audio.delta` (and legacy `response.audio.delta`), plus transcript/text delta events.
The connection is fully duplex: the server pushes deltas continuously while the client can send `input_audio_buffer.append` / interruption events at any time.

## Relevance to this repo (app/routes/realtime.py; websockets additional_headers note; REALTIME_MODEL env)
- `app/routes/realtime.py` implements a **WebSocket relay**: it accepts a client WS at `/v1/realtime/ws?model=...&session_id=...`, validates the model against `ALLOWED_REALTIME_MODELS`, then opens an upstream WS to `{ws_base}/v1/realtime?model=...&session_id=...` and bidirectionally pipes text frames.
- **`additional_headers` (not `extra_headers`)**: the upstream connect uses `ws_connect(url, additional_headers=headers, subprotocols=...)` (realtime.py:399). This is deliberate — the Python `websockets` library **renamed `extra_headers` → `additional_headers` in v14+** (new asyncio client). `pyproject.toml` pins `websockets>=15,<17` with a comment documenting exactly this dependency. Using `extra_headers` on websockets 15+ would raise `TypeError`. Note: `chatgpt_baseline.md` (a captured baseline snapshot) still shows the OLD `extra_headers` form at lines ~4678/7243 — that is stale and would break against the pinned websockets version; the live `app/routes/realtime.py` is the correct one.
- **`REALTIME_MODEL` env:** `DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-realtime")` (realtime.py:36). `.env.example.env` and `render.yaml` set `REALTIME_MODEL=gpt-realtime`. Note an inconsistency: `app/core/config.py:325` defaults `REALTIME_MODEL` to the older `gpt-4o-realtime-preview`, so the effective default depends on which loader path runs — worth reconciling.
- Upstream auth passes through the client `Authorization` header or falls back to `OPENAI_API_KEY`, and sets `OpenAI-Beta: realtime=v1` (`OPENAI_REALTIME_BETA`, realtime.py:34/392). Subprotocols advertised: `openai-realtime-v1`, `realtime`.
- `ALLOWED_REALTIME_MODELS` = {`gpt-realtime`, `gpt-realtime-2025-08-28`, `gpt-realtime-mini`, `gpt-realtime-mini-2025-10-06`, `gpt-realtime-mini-2025-12-15`}. This set does NOT yet include `gpt-realtime-2.1` / `gpt-realtime-2.1-mini` — a request for the newest tier would be rejected until added.

## Verify / TODO
- [ ] Re-fetch `platform.openai.com/docs/guides/realtime` (currently 403) to confirm the canonical transport/event wording rather than relying on web-search summaries.
- [ ] Confirm whether `gpt-realtime-2.1` / `gpt-realtime-2.1-mini` should be added to `ALLOWED_REALTIME_MODELS` and whether it becomes the default.
- [ ] Reconcile the two `REALTIME_MODEL` defaults (`gpt-realtime` in realtime.py vs `gpt-4o-realtime-preview` in config.py:325).
- [ ] The GA session schema `RealtimeSessionCreateRequestGA` vs beta `RealtimeSessionCreateRequest` suggests a beta→GA migration; verify which shape the relay's clients send.
- [ ] Optional: pull a concrete cookbook realtime example (openai-cookbook) for canonical event sequencing.
