# client.py

import os
import requests

RELAY_URL = os.getenv("RELAY_URL", "http://localhost:7777")  # Change port as needed
API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")              # Put your OpenAI key here

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Example: Chat completion relay
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"}
    ]
}

r = requests.post(
    f"{RELAY_URL}/v1/chat/completions",
    json=payload,
    headers=headers,
    timeout=60
)
print("Status:", r.status_code)
print("Response:", r.json())

# Example: Test Assistants endpoint (requires OpenAI-Beta header)
assist_headers = headers.copy()
assist_headers["OpenAI-Beta"] = "assistants=v2"

r2 = requests.get(
    f"{RELAY_URL}/v1/assistants",
    headers=assist_headers,
    timeout=60
)
print("Assistants status:", r2.status_code)
try:
    print("Assistants response:", r2.json())
except Exception:
    print("Raw:", r2.text)
