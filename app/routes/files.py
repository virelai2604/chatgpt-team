# app/routes/files.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from io import BytesIO

router = APIRouter()

# In-memory file store: {file_id: {"content": bytes, "filename": str, ...}}
file_store = {}

@router.post("/files")
async def upload_file(file: UploadFile = File(...), purpose: str = Form(...)):
    content = await file.read()
    file_id = "file-123"  # In real use, make this unique (uuid, etc.)
    file_store[file_id] = {
        "content": content,
        "filename": file.filename,
        "purpose": purpose,
        "size": len(content),
        "object": "file",
    }
    return JSONResponse(content={
        "id": file_id,
        "object": "file",
        "bytes": len(content),
        "filename": file.filename,
        "purpose": purpose,
        "status": "uploaded"
    })

@router.get("/files")
async def list_files():
    return {
        "data": [
            {
                "id": file_id,
                "object": "file",
                "bytes": file_info["size"],
                "filename": file_info["filename"],
                "purpose": file_info["purpose"],
                "status": "uploaded"
            }
            for file_id, file_info in file_store.items()
        ]
    }

@router.get("/files/{file_id}/content")
async def download_file(file_id: str):
    file_info = file_store.get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return StreamingResponse(BytesIO(file_info["content"]), media_type="application/octet-stream", headers={
        "Content-Disposition": f'attachment; filename="{file_info["filename"]}"'
    })
