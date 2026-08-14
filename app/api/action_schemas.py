# app/api/action_schemas.py
"""Request-body schemas for the routes exposed to ChatGPT Actions.

Why this exists
---------------
The relay's write routes read the raw request body (`await request.body()`)
rather than declaring a pydantic model, because it is a transparent proxy: it
forwards whatever the caller sent and lets OpenAI decide what is valid. That is
the right runtime behaviour, but it left the generated OpenAPI document with no
`requestBody` at all on those operations.

For a human reading `/docs` that is merely unhelpful. For ChatGPT Actions it is
fatal: the model builds the request from the schema, so an operation with no
declared body gets called with no body. `POST /v1/responses` — the endpoint
`static/.well-known/ai-plugin.json` tells models to prefer — was among them.

These schemas are attached via each route's `openapi_extra`, which changes the
document only. No validation is added, nothing is parsed differently, and the
handlers are untouched.

Provenance
----------
Field names, types and `required` lists are taken from OpenAI's own published
spec — `api_reference/openapi.transformed.yml` in openai/openai-python, the
same document that generates the SDK. The relevant component schemas are
`CreateResponse`, `CreateEmbeddingRequest`, `CreateImageRequest`,
`RealtimeSessionCreateRequest` and `CreateVideoMultipartBody`.

They are deliberately *not* verbatim copies. `CreateResponse` alone pulls in 203
component schemas and ~141 KB once its `$ref` graph is resolved; inlining that
into a 13-path Actions document would dwarf everything else in it, and ChatGPT
has to parse the whole document on import. What is kept is the subset a model
actually needs to construct a sensible call.

Every schema sets `additionalProperties: true` on purpose. The relay does not
validate, so any parameter the SDK supports — and any parameter OpenAI adds
later — still passes straight through. Omitting a field here restricts what
ChatGPT will *suggest*, never what the relay will *accept*.
"""

from __future__ import annotations

from typing import Any, Dict

_SPEC = "openai/openai-python api_reference/openapi.transformed.yml"


def _json_body(schema: Dict[str, Any], *, required: bool = True) -> Dict[str, Any]:
    """Wrap a schema in the `openapi_extra` shape FastAPI merges into the doc."""
    return {"requestBody": {"required": required, "content": {"application/json": {"schema": schema}}}}


# --- /v1/responses ---------------------------------------------------------
# Source: CreateResponse. `model` and `input` are the pair that matters; the
# upstream schema marks nothing required because it also accepts a bare
# `prompt` reference, but a model calling this relay needs to be told to send
# them or it will send an empty object.
RESPONSES_BODY = _json_body(
    {
        "type": "object",
        "title": "CreateResponse",
        "description": f"Body for POST /v1/responses. Subset of CreateResponse in {_SPEC}.",
        "properties": {
            "model": {
                "type": "string",
                "description": "Model ID, e.g. gpt-5.5. Defaults to the relay's DEFAULT_MODEL when omitted.",
            },
            "input": {
                "description": "A string prompt, or the structured input array the Responses API accepts.",
                "anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}],
            },
            "instructions": {"type": "string", "description": "System-level instructions for the model."},
            "stream": {
                "type": "boolean",
                "description": "Stream the response as SSE. Prefer /v1/actions/responses/stream for Actions.",
            },
            "store": {"type": "boolean", "description": "Persist the response for later retrieval."},
            "previous_response_id": {"type": "string", "description": "Continue from an earlier response."},
            "conversation": {"description": "Conversation this response belongs to."},
            "max_output_tokens": {"type": "integer", "minimum": 1},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
            "top_p": {"type": "number", "minimum": 0, "maximum": 1},
            "tools": {"type": "array", "items": {"type": "object"}},
            "tool_choice": {"description": "auto | none | required, or a specific tool."},
            "parallel_tool_calls": {"type": "boolean"},
            "reasoning": {"type": "object", "description": "Reasoning options for reasoning-capable models."},
            "text": {"type": "object", "description": "Text output options, including response format."},
            "metadata": {"type": "object"},
        },
        "additionalProperties": True,
    }
)

# The SSE wrapper takes the same body and forces stream=True server-side, so
# `stream` is not advertised here — setting it would be a no-op at best.
RESPONSES_STREAM_BODY = _json_body(
    {
        "type": "object",
        "title": "CreateResponseStream",
        "description": (
            "Body for the SSE wrapper. Identical to POST /v1/responses except that the relay "
            f"sets stream=true itself. Subset of CreateResponse in {_SPEC}."
        ),
        "properties": {
            k: v for k, v in RESPONSES_BODY["requestBody"]["content"]["application/json"]["schema"]["properties"].items()
            if k != "stream"
        },
        "additionalProperties": True,
    }
)

# --- /v1/embeddings --------------------------------------------------------
# Source: CreateEmbeddingRequest. required: [model, input]
EMBEDDINGS_BODY = _json_body(
    {
        "type": "object",
        "title": "CreateEmbeddingRequest",
        "description": f"Body for POST /v1/embeddings. From CreateEmbeddingRequest in {_SPEC}.",
        "required": ["model", "input"],
        "properties": {
            "model": {"type": "string", "description": "Embedding model ID, e.g. text-embedding-3-small."},
            "input": {
                "description": "Text to embed: a string, an array of strings, or pre-tokenised integer arrays.",
                "anyOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "array", "items": {"type": "integer"}},
                ],
            },
            "encoding_format": {"type": "string", "enum": ["float", "base64"], "default": "float"},
            "dimensions": {"type": "integer", "minimum": 1, "description": "Truncate embeddings to this many dimensions."},
            "user": {"type": "string"},
        },
        "additionalProperties": True,
    }
)

# --- /v1/images/generations ------------------------------------------------
# Source: CreateImageRequest. required: [prompt]
IMAGES_GENERATIONS_BODY = _json_body(
    {
        "type": "object",
        "title": "CreateImageRequest",
        "description": f"Body for POST /v1/images/generations. From CreateImageRequest in {_SPEC}.",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "A text description of the desired image(s)."},
            "model": {"type": "string", "description": "Image model ID, e.g. gpt-image-1."},
            "n": {"type": "integer", "minimum": 1, "maximum": 10, "default": 1},
            "size": {"type": "string", "description": "e.g. 1024x1024, 1536x1024, 1024x1536, or auto."},
            "quality": {"type": "string", "description": "e.g. low, medium, high, or auto."},
            "background": {"type": "string", "enum": ["transparent", "opaque", "auto"]},
            "output_format": {"type": "string", "description": "e.g. png, jpeg, webp."},
            "output_compression": {"type": "integer", "minimum": 0, "maximum": 100},
            "response_format": {"type": "string", "enum": ["url", "b64_json"]},
            "moderation": {"type": "string"},
            "style": {"type": "string"},
            "user": {"type": "string"},
        },
        "additionalProperties": True,
    }
)

# --- /v1/realtime/sessions -------------------------------------------------
# Source: RealtimeSessionCreateRequest. Upstream marks client_secret required,
# but the relay mints the session on the caller's behalf and defaults `model`
# to REALTIME_MODEL, so nothing is required of an Actions caller here.
REALTIME_SESSION_BODY = _json_body(
    {
        "type": "object",
        "title": "RealtimeSessionCreateRequest",
        "description": (
            "Body for POST /v1/realtime/sessions. Subset of RealtimeSessionCreateRequest in "
            f"{_SPEC}. The relay supplies credentials and defaults `model` to REALTIME_MODEL, "
            "so an empty object is a valid request."
        ),
        "properties": {
            "model": {"type": "string", "description": "Realtime model ID, e.g. gpt-realtime."},
            "modalities": {"type": "array", "items": {"type": "string"}, "description": 'e.g. ["text", "audio"].'},
            "instructions": {"type": "string"},
            "voice": {"type": "string"},
            "input_audio_format": {"type": "string"},
            "output_audio_format": {"type": "string"},
            "input_audio_transcription": {"type": "object"},
            "turn_detection": {"type": "object"},
            "tools": {"type": "array", "items": {"type": "object"}},
            "tool_choice": {"description": "auto | none | required, or a specific tool."},
            "temperature": {"type": "number"},
            "speed": {"type": "number"},
            "max_response_output_tokens": {"description": "An integer, or the string 'inf'."},
        },
        "additionalProperties": True,
    },
    required=False,
)

# --- /v1/actions/videos ----------------------------------------------------
# Source: CreateVideoMultipartBody. NOTE: openai/openai-python@721cb1cd stamps
# `deprecated: true` on the video paths — the Sora APIs shut down in September.
# The schema is documented because the routes still work today; whether the
# relay should keep advertising them to ChatGPT is a separate decision.
VIDEOS_CREATE_BODY = _json_body(
    {
        "type": "object",
        "title": "CreateVideo",
        "description": (
            f"Body for POST /v1/actions/videos. From CreateVideoMultipartBody in {_SPEC}. "
            "DEPRECATED upstream: the Sora video APIs are scheduled for shutdown in September."
        ),
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "Text description of the video to generate."},
            "model": {"type": "string", "description": "Video model ID."},
            "seconds": {"description": "Clip duration."},
            "size": {"type": "string", "description": "Output resolution, e.g. 1280x720."},
        },
        "additionalProperties": True,
    }
)

VIDEOS_REMIX_BODY = _json_body(
    {
        "type": "object",
        "title": "RemixVideo",
        "description": (
            "Body for POST /v1/actions/videos/{video_id}/remix. "
            "DEPRECATED upstream: the Sora video APIs are scheduled for shutdown in September."
        ),
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "How the source video should be changed."}
        },
        "additionalProperties": True,
    }
)
