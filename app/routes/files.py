from fastapi import APIRouter, UploadFile, File, HTTPException
from app.client import OpenAIClient
import os

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    api_key = os.getenv("OPENAI_API_KEY", "sk-...")
    client = OpenAIClient(api_key)

    try:
        file_bytes = await file.read()
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        files = {
            "file": (file.filename, file_bytes, file.content_type),
            "purpose": (None, "fine-tune")  # Required by OpenAI API
        }
        response = await client.client.post("/files", headers=headers, files=files)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
