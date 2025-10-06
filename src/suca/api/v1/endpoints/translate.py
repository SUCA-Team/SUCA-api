from fastapi import APIRouter, Request
from pylingva import pylingva

router = APIRouter(prefix="/translate", tags=["Translate"])
trans = pylingva()

@router.get("/en2jp")
async def translate_text(request: Request, q: str | None = None, target_lang: str = "ja"):
    if q is None:
        return {"Please enter text!"}
    
    ip = q
    return {
        "original": ip,
        "translated": trans.translate("en", target_lang, ip)
    }

@router.get("/jp2en")
async def translate_text(request: Request, q: str | None = None, target_lang: str = "en"):
    if q is None:
        return {"Please enter text!"}
    
    ip = q
    return {
        "original": ip,
        "translated": trans.translate("ja", target_lang, ip)
    }