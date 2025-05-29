from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="Broma Api", description="API для работы с Broma релизами и доставками")

BASE_URL = "https://api-rod.broma16.ru/api/accounts/629401"
HEADERS_TEMPLATE = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://rod.broma16.ru",
    "Referer": "https://rod.broma16.ru/",
}

example_release_success = {
    "status": "ok",
    "data": {
        "status": "ok",
        "total": 1,
        "data": [
            {
                "id": 6008176,
                "title": "!ledledled",
                "subtitle": "prod. by SHEEPY",
                "release_type_id": 51,
                "performers": ["merccifuul"],
                "published_date": "2022-01-01",
                "grid": "",
                "ean": "5063015274090",
                "moderation_status": "approved",
                "label_id": 629401,
                "label": "ООО \"РУ ТОЧКА МЕДИА\"",
                "has_pendings": False,
                "genres": [23],
                "sale_start_dates": [{"date": "2022-04-15", "territories": [17]}],
                "statuses": ["takendown", "approved", "ready"],
                "catalogue_number": "R27304",
                "artists": [{"id": 601431, "title": "merccifuul", "account_id": 643453}]
            }
        ],
        "items": 1,
        "page": 1
    }
}

example_release_not_found = {
    "status": "ok",
    "data": {
        "status": "ok",
        "total": 0,
        "data": [],
        "items": 0,
        "page": 1
    }
}

example_deliveries_success = {
    "status": "ok",
    "data": [
        {
            "sender_id": 149916,
            "recipient_id": 25240,
            "status": "shipping",
            "delivery_id": 63281,
            "date": "2025-03-17 09:12:47",
            "recipient_title": "Tidal Music AS",
            "sender_title": "Broma 16 NL B.V."
        },
        {
            "sender_id": 149916,
            "recipient_id": 49803,
            "status": "shipping",
            "delivery_id": 63309,
            "date": "2025-03-17 09:30:44",
            "recipient_title": "Apple Music",
            "sender_title": "Broma 16 NL B.V."
        }
    ]
}

example_takedown_success = {
    "status": "ok",
    "message": "Takedown request submitted successfully"
}

example_error_invalid_token = {
    "detail": "Invalid or expired access token"
}

example_error_release_not_found = {
    "detail": "Release not found"
}

example_error_takedown_conflict = {
    "detail": "Release already taken down (no shipping outlets found)"
}

example_error_takedown_failed = {
    "message": "Ошибка при выполнении takedown запроса",
    "broma_error": {
        "error_code": 123,
        "error_message": "Detailed error from Broma API"
    }
}

async def get_release_id(upc_code: str, access_token: str):
    headers = HEADERS_TEMPLATE.copy()
    headers["X-Access-Token"] = access_token
    url = f"{BASE_URL}/assets"
    params = {"type": "releases", "search": upc_code}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)

    if response.status_code == 500:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching release data")

    data = response.json()
    total = data.get("data", {}).get("total", 0)
    if total == 0:
        raise HTTPException(status_code=404, detail="Release not found")

    releases = data.get("data", {}).get("data", [])
    return releases[0]["id"]

@app.get(
    "/release",
    summary="Get metadata release",
    tags=["Release"],
    responses={
        200: {"description": "Successful response with release metadata", "content": {"application/json": {"example": example_release_success}}},
        401: {"description": "Invalid or expired access token", "content": {"application/json": {"example": example_error_invalid_token}}},
        404: {"description": "Release not found", "content": {"application/json": {"example": example_release_not_found}}},
    }
)
async def get_release(
    upc_code: str = Query(..., description="UPC code релиза"),
    access_token: str = Query(..., description="Токен доступа для API Broma"),
):
    headers = HEADERS_TEMPLATE.copy()
    headers["X-Access-Token"] = access_token
    url = f"{BASE_URL}/assets"
    params = {"type": "releases", "search": upc_code}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка при получении данных с Broma API")

    json_response = response.json()
    total = json_response.get("data", {}).get("total", 0)
    if total == 0:
        return JSONResponse(status_code=404, content=json_response)

    return json_response.get("data", {}).get("data", [])

@app.get(
    "/release_deliveries",
    summary="Get deliveries release",
    tags=["Deliveries"],
    responses={
        200: {"description": "Successful response with release deliveries", "content": {"application/json": {"example": example_deliveries_success}}},
        401: {"description": "Invalid or expired access token", "content": {"application/json": {"example": example_error_invalid_token}}},
        404: {"description": "Release not found", "content": {"application/json": {"example": example_error_release_not_found}}},
    }
)
async def get_release_deliveries(
    upc_code: str = Query(..., description="UPC code релиза"),
    access_token: str = Query(..., description="Токен доступа для API Broma"),
):
    release_id = await get_release_id(upc_code, access_token)

    headers = HEADERS_TEMPLATE.copy()
    headers["X-Access-Token"] = access_token
    url = f"{BASE_URL}/releases/{release_id}/outlets/deliveries"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 500:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка при получении данных с Broma API")

    return response.json()

@app.post(
    "/release_takedown",
    summary="Release takedown",
    tags=["Takedown"],
    responses={
        200: {"description": "Successful takedown request", "content": {"application/json": {"example": example_takedown_success}}},
        401: {"description": "Invalid or expired access token", "content": {"application/json": {"example": example_error_invalid_token}}},
        409: {"description": "Release already taken down", "content": {"application/json": {"example": example_error_takedown_conflict}}},
        400: {"description": "Takedown request error", "content": {"application/json": {"example": example_error_takedown_failed}}},
    }
)
async def release_takedown(
    upc_code: str = Query(..., description="UPC code релиза"),
    access_token: str = Query(..., description="Токен доступа для API Broma"),
    hmac_hash: str = Header(..., alias="HMAC-Hash", description="HMAC Hash заголовок"),
    hmac_timestamp: str = Header(..., alias="HMAC-Timestamp", description="HMAC Timestamp заголовок"),
):
    release_id = await get_release_id(upc_code, access_token)

    headers = HEADERS_TEMPLATE.copy()
    headers["X-Access-Token"] = access_token
    headers["HMAC-Hash"] = hmac_hash
    headers["HMAC-Timestamp"] = hmac_timestamp

    url_deliveries = f"{BASE_URL}/releases/{release_id}/outlets/deliveries"

    async with httpx.AsyncClient() as client:
        response_deliveries = await client.get(url_deliveries, headers=headers)

    if response_deliveries.status_code == 500:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    elif response_deliveries.status_code != 200:
        raise HTTPException(status_code=response_deliveries.status_code, detail="Ошибка при получении данных с Broma API")

    deliveries_data = response_deliveries.json()
    shipping_outlets = [
        item["recipient_id"]
        for item in deliveries_data.get("data", [])
        if item.get("status") == "shipping"
    ]

    if not shipping_outlets:
        return JSONResponse(
            status_code=409,
            content={"detail": "Release already taken down (no shipping outlets found)"}
        )

    url_takedown = f"{BASE_URL}/releases/{release_id}/queues/takedowns"
    body = {
        "outlets": shipping_outlets,
        "reason": {"id": "1", "message": ""}
    }
    headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient() as client:
        response_takedown = await client.post(url_takedown, json=body, headers=headers)

    if response_takedown.status_code == 500:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    elif response_takedown.status_code != 200:
        try:
            error_detail = response_takedown.json()
        except Exception:
            error_detail = response_takedown.text

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Ошибка при выполнении takedown запроса",
                "broma_error": error_detail
            }
        )

    return response_takedown.json()
