import httpx
import asyncio

class OpenAIRelayClient:
    def __init__(self, base_url="http://localhost:8000/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(15.0)
        )

    async def post(self, path: str, payload: dict, retries: int = 3):
        for attempt in range(1, retries + 1):
            try:
                response = await self.client.post(path, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if response.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    wait = 2 ** attempt
                    print(f"⏳ Retry {attempt}/{retries} in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    print(f"❌ HTTP Error: {e}")
                    raise

    async def close(self):
        await self.client.aclose()

# --- Example test usage ---
async def main():
    client = OpenAIRelayClient()  # Defaults to localhost relay
    # For /v1/chat/completions
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello from test client!"}]
    }
    try:
        result = await client.post("/chat/completions", payload)
        print(result)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
