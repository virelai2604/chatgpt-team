from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request
import httpx
import os

router = APIRouter()

@router.api_route("/generations", methods=["POST"])
async def image_generations(request: Request):
    # Structured log for image generations
    try:
        body = await request.json()
        save_chat_request(
            role="user",
            content=str(body.get("prompt", "")),
            function_call_json="",
            metadata_json=str(body)
        )
    except Exception as ex:
        print("BIFL log error (image generations):", ex)
    # Universal raw logging handled in forward_openai
    return await forward_openai(request, "/v1/images/generations")

@router.get("/{image_id}/content")
async def stream_image(image_id: str):
    """
    BIFL-style image streaming endpoint.
    Streams either from local disk or a remote CDN/URL based on environment config.
    Supports both PNG and JPEG.
    """
    IMAGE_MODE = os.getenv("IMAGE_STREAM_MODE", "local")
    IMAGE_DIR = os.getenv("IMAGE_STREAM_DIR", "/images")
    IMAGE_URL_TEMPLATE = os.getenv("IMAGE_STREAM_URL", "https://cdn.yourapp.com/images/{image_id}.{ext}")

    # Try .png first, then .jpg/.jpeg
    for ext, mime in [("png", "image/png"), ("jpg", "image/jpeg"), ("jpeg", "image/jpeg")]:
        if IMAGE_MODE == "local":
            image_path = os.path.join(IMAGE_DIR, f"{image_id}.{ext}")
            if os.path.isfile(image_path):
                def iterfile():
                    with open(image_path, "rb") as f:
                        while chunk := f.read(4096):
                            yield chunk
                return StreamingResponse(iterfile(), media_type=mime)
        elif IMAGE_MODE == "remote":
            image_url = IMAGE_URL_TEMPLATE.format(image_id=image_id, ext=ext)
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url, stream=True)
                if resp.status_code == 200:
                    return StreamingResponse(resp.aiter_bytes(), media_type=mime)

    raise HTTPException(status_code=404, detail="Image not found")
