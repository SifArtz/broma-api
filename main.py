from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional
import httpx

app = FastAPI(
    title="Broma API",
    description="API для управления релизами Broma",
    version="1.0.0"
)

BASE_URL = "https://api-rod.broma16.ru/api/accounts/629401"
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://rod.broma16.ru",
    "Referer": "https://rod.broma16.ru/",
}


# ========================
# Utility: fetch_from_broma
# ========================
async def fetch_from_broma(
    url: str,
    access_token: str,
    headers_extra: Optional[dict] = None,
    params: Optional[dict] = None,
    method: str = "GET",
    body: Optional[dict] = None
):
    headers = COMMON_HEADERS.copy()
    headers["X-Access-Token"] = access_token
    if headers_extra:
        headers.update(headers_extra)

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = await client.post(url, headers=headers, json=body)
        else:
            raise ValueError("Unsupported HTTP method")

    if response.status_code in (401, 500):
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


# ========================
# Utility: resolve_release_id
# ========================
async def resolve_release_id(upc_code: str, access_token: str) -> int:
    response_data = await fetch_from_broma(
        url=f"{BASE_URL}/assets",
        access_token=access_token,
        params={"type": "releases", "search": upc_code}
    )
    total = response_data.get("data", {}).get("total", 0)
    releases = response_data.get("data", {}).get("data", [])
    if total == 0 or not releases:
        raise HTTPException(status_code=404, detail="Release not found")
    return releases[0]["id"]


# ========================
# /release
# ========================
@app.get(
    "/release",
    summary="Получить метаданные релиза",
    tags=["Release"],
    responses={
        200: {
            "description": "Метаданные релиза успешно получены",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 6008176,
                            "title": "!ledledled",
                            "subtitle": "prod. by SHEEPY",
                            "release_type_id": 51,
                            "performers": ["merccifuul"],
                            "published_date": "2022-01-01",
                            "ean": "5063015274090",
                            "moderation_status": "approved",
                            "label": "ООО \"РУ ТОЧКА МЕДИА\""
                        }
                    ]
                }
            }
        },
        401: {
            "description": "Невалидный или просроченный токен",
            "content": {"application/json": {"example": {"detail": "Invalid or expired access token"}}}
        },
        404: {
            "description": "Релиз не найден",
            "content": {"application/json": {"example": {"detail": "Release not found"}}}
        }
    }
)
async def get_release(
    upc_code: str = Query(..., description="UPC-код релиза"),
    access_token: str = Query(..., description="API токен доступа")
):
    data = await fetch_from_broma(
        url=f"{BASE_URL}/assets",
        access_token=access_token,
        params={"type": "releases", "search": upc_code}
    )
    releases = data.get("data", {}).get("data", [])
    if not releases:
        return JSONResponse(status_code=404, content={"detail": "Release not found"})
    return releases


# ========================
# /release_deliveries
# ========================
@app.get(
    "/release_deliveries",
    summary="Получить список доставок релиза",
    tags=["Deliveries"],
    responses={
        200: {
            "description": "Список доставок успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "data": [
                            {
                                "sender_id": 149916,
                                "recipient_id": 25240,
                                "status": "shipping",
                                "delivery_id": 63281,
                                "date": "2025-03-17 09:12:47",
                                "recipient_title": "Tidal Music AS"
                            }
                        ]
                    }
                }
            }
        },
        401: {
            "description": "Невалидный токен",
            "content": {"application/json": {"example": {"detail": "Invalid or expired access token"}}}
        },
        404: {
            "description": "Релиз не найден",
            "content": {"application/json": {"example": {"detail": "Release not found"}}}
        }
    }
)
async def get_release_deliveries(
    upc_code: str = Query(..., description="UPC-код релиза"),
    access_token: str = Query(..., description="API токен доступа")
):
    release_id = await resolve_release_id(upc_code, access_token)
    deliveries = await fetch_from_broma(
        url=f"{BASE_URL}/releases/{release_id}/outlets/deliveries",
        access_token=access_token
    )
    return deliveries


# ========================
# /release_takedown
# ========================
@app.post(
    "/release_takedown",
    summary="Снять релиз с площадок",
    tags=["Takedown"],
    responses={
        200: {
            "description": "Запрос на снятие релиза успешно выполнен",
            "content": {"application/json": {"example": {"status": "ok", "message": "Takedown request submitted successfully"}}}
        },
        401: {
            "description": "Невалидный токен",
            "content": {"application/json": {"example": {"detail": "Invalid or expired access token"}}}
        },
        409: {
            "description": "Релиз уже снят",
            "content": {"application/json": {"example": {"detail": "Release already taken down (no shipping outlets found)"}}}
        },
        400: {
            "description": "Ошибка при отправке запроса",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Error while executing takedown request",
                        "broma_error": {
                            "error_code": 123,
                            "error_message": "Detailed error from Broma API"
                        }
                    }
                }
            }
        }
    }
)
async def takedown_release(
    upc_code: str = Query(..., description="UPC-код релиза"),
    access_token: str = Query(..., description="API токен доступа"),
    hmac_hash: str = Header(..., alias="HMAC-Hash", description="Заголовок HMAC-Hash"),
    hmac_timestamp: str = Header(..., alias="HMAC-Timestamp", description="Заголовок HMAC-Timestamp")
):
    release_id = await resolve_release_id(upc_code, access_token)

    deliveries_data = await fetch_from_broma(
        url=f"{BASE_URL}/releases/{release_id}/outlets/deliveries",
        access_token=access_token,
        headers_extra={
            "HMAC-Hash": hmac_hash,
            "HMAC-Timestamp": hmac_timestamp
        }
    )

    shipping_outlets = [
        item["recipient_id"]
        for item in deliveries_data.get("data", [])
        if item.get("status") == "shipping"
    ]

    if not shipping_outlets:
        raise HTTPException(
            status_code=409,
            detail="Release already taken down (no shipping outlets found)"
        )

    takedown_body = {
        "outlets": shipping_outlets,
        "reason": {"id": "1", "message": ""}
    }

    takedown_response = await fetch_from_broma(
        url=f"{BASE_URL}/releases/{release_id}/queues/takedowns",
        access_token=access_token,
        headers_extra={
            "HMAC-Hash": hmac_hash,
            "HMAC-Timestamp": hmac_timestamp
        },
        method="POST",
        body=takedown_body
    )

    return takedown_response
