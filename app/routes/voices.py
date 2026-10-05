from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.tts.registry import list_all_voices

router = APIRouter()

@router.get("/voices")
def get_voices(lang: str = Query(None)):
    voices = list_all_voices()
    if lang:
        voices = [v for v in voices if v.language == lang]
    res = [{
        "id": v.id,
        "engine": v.engine,
        "language": v.language,
        "locale": v.locale,
        "gender": v.gender,
        "name": v.name,
        "description": v.description,
    } for v in voices]
    return JSONResponse(res)
