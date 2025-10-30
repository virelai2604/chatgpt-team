import httpx, asyncio

async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            "https://chatgpt-team-relay.onrender.com/v1/responses",
            json={
                "model": "gpt-5",
                "input": "Stream a haiku about electrons.",
                "stream": True
            }
        ) as response:
            async for line in response.aiter_text():
                print(line.strip())

if __name__ == "__main__":
    asyncio.run(main())
