from fastapi import UploadFile, File, HTTPException, Form, APIRouter
from .s3_utils import upload_multiple_files, upload_or_replace_file, delete_file

file_router = APIRouter()

@file_router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    key: str = Form(...),
    replace: bool = Form(True),
):
    try:
        url = await upload_or_replace_file(file, key=key, replace=replace)
        return {"url": url, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@file_router.delete("/delete")
async def delete(key: str):
    success = await delete_file(key)
    if success:
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="File not found or couldn't be deleted")
    

@file_router.post("/upload_multiple")
async def upload_multiple(
    files: list[UploadFile] = File(...),
    keys: list[str] = Form(...),
    replace: bool = Form(True),
):
    if len(files) != len(keys):
        raise HTTPException(status_code=400, detail="Number of files and keys must match")
    
    urls = await upload_multiple_files(files, keys, replace)
    return {"urls": urls, "status": "success"}