import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse

DATA_DIR = "data/banners"
os.makedirs(DATA_DIR, exist_ok=True)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

router = APIRouter()

@router.post("/admin/banners/upload")
def upload_banner_image(image: UploadFile = None):
    if image is None:
        from fastapi import File
        image = File(...)
    ext = image.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return JSONResponse({"error": "unsupported file"}, status_code=400)
    fname = f"{uuid.uuid4().hex}.{ext}"
    fpath = os.path.join(DATA_DIR, fname)
    with open(fpath, "wb") as f:
        shutil.copyfileobj(image.file, f)
    return {"filename": fname, "url": f"/data/banners/{fname}"}

@router.get("/go/banner/{banner_id}")
def banner_redirect(banner_id: int):
    # dummy redirect (логика stats и проверки по БД реализуется на сл. этапе)
    return RedirectResponse("https://yandex.ru", status_code=302)
