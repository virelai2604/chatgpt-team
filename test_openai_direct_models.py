# test_openai_direct_models.py
"""
Minimal direct call to OpenAI's /v1/models from the same environment
used by your relay. This bypasses the relay completely.

Requires:
  - openai==2.8.1
  - OPENAI_API_KEY in your environment
"""

import os
from openai import OpenAI
from openai._exceptions import APIStatusError

def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set in this shell environment.")

    client = OpenAI(api_key=api_key)

    print("Calling OpenAI /v1/models directly ...")
    try:
        resp = client.models.list()
    except APIStatusError as e:
        # This will show the real 403 payload if it's JSON
        print(f"Status error: {e.status_code}")
        print(f"Error message: {e.message}")
        if e.response is not None:
            print("Raw response text:")
            print(e.response.text)
        raise SystemExit(1)
    except Exception as e:  # network / other issues
        print(f"Unexpected exception during /v1/models: {type(e).__name__}: {e}")
        raise SystemExit(1)

    # If we reach here, status_code was 200
    print(f"/v1/models OK. Received {len(resp.data)} models.")
    # Optionally print a few IDs
    for model in resp.data[:5]:
        print(" -", model.id)

if __name__ == "__main__":
    main()
