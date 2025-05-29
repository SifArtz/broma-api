from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import List, Optional
import httpx

app = FastAPI(
    title="Broma API",
    description="API для работы с Broma",
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
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                headers["Content-Type"] = "application/json"
                response = await client.post(url, headers=headers, json=body)
            else:
                raise ValueError("Unsupported HTTP method")

        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Request error: {exc}")

    if response.status_code == 401 or response.status_code == 500:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error from Broma API: {response.text}"
        )

    return response.json()


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


@app.get("/release", tags=["Release"], summary="Получить метаданные релиза")
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


@app.get("/release_deliveries", tags=["Deliveries"], summary="Получить доставки релиза")
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


@app.post("/release_takedown", tags=["Takedown"], summary="Снять релиз с платформ")
async def takedown_release(
    upc_code: str = Query(..., description="UPC-код релиза"),
    access_token: str = Query(..., description="API токен доступа"),
    hmac_hash: str = Header(..., alias="HMAC-Hash", description="HMAC-хеш заголовок"),
    hmac_timestamp: str = Header(..., alias="HMAC-Timestamp", description="HMAC-временная метка")
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
