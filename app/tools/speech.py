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
def run(payload):
    """Simulates /v1/audio/speech call."""
    text = payload.get("text", "")
    return {
        "id": "sp_mock_001",
        "object": "audio",
        "url": f"https://mock-audio.local/{text[:10] or 'speech'}.mp3"
    }
