TOOL_ID = "speech"
TOOL_VERSION = "v1"
TOOL_TYPE = "audio"
TOOL_SCHEMA = {
    "name": "speech",
    "description": "Convert text to speech using OpenAI's TTS API.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "voice": {"type": "string", "default": "verse"}
        },
        "required": ["text"]
    },
    "returns": {"type": "object", "properties": {"audio_url": {"type": "string"}}}
}
