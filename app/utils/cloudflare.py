import httpx

async def purge_cache(zone_id, url, token):
    async with httpx.AsyncClient() as client:
        return await client.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache',
            headers={'Authorization': f'Bearer {token}'},
            json={'files': [url]}
        )
