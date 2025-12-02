# from fastapi import APIRouter, Request
# from pylingva import pylingva

# router = APIRouter(prefix="/translate", tags=["Translate"])
# trans = pylingva()

# @router.get("/en2jp")
# async def translate_en2jp(request: Request, q: str | None = None, target_lang: str = "ja") -> dict:
#     if q is None:
#         return {
#             "notification": "Please enter text!"
#         }

#     ip = q
#     return {
#         "original": ip,
#         "translated": trans.translate("en", target_lang, ip)
#     }

# @router.get("/jp2en")
# async def translate_jp2en(request: Request, q: str | None = None, target_lang: str = "en") -> dict:
#     if q is None:
#         return {
#             "notification": "Please enter text!"
#         }

#     ip = q
#     return {
#         "original": ip,
#         "translated": trans.translate("ja", target_lang, ip)
#     }
