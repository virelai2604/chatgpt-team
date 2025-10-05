from fastapi import APIRouter, Request, Response
import httpx

router = APIRouter()

@router.api_route('/v1/{rest_of_path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def passthrough_proxy(rest_of_path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f'https://api.openai.com/v1/{rest_of_path}'
        resp = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body()
        )
    return Response(resp.content, status_code=resp.status_code, headers=dict(resp.headers))
