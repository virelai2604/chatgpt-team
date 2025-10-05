import httpx
import os
import asyncio

class OpenAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.org_id = os.getenv("OPENAI_ORG_ID")
        self.allowed_models = os.getenv("MODEL_ALLOWLIST", "").split(",")
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._build_headers(),
            timeout=httpx.Timeout(15.0)
        )

    def _build_headers(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id
        return headers

    #def _guard_model(self, payload: dict):
        #model = payload.get("model")
        #if model and model not in self.allowed_models:
            #raise ValueError(f"🚫 Model '{model}' not in allowlist.")

    async def post(self, path: str, payload: dict, retries: int = 3):
        self._guard_model(payload)

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
                    raise e
