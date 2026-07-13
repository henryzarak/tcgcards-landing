from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from functools import lru_cache

app = FastAPI(title="TCG Cards API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

AIRTABLE_TOKEN = "os.environ.get("AIRTABLE_API_KEY", "")"
BASE_ID = "appCXMRLvsM7p6gtA"
TABLE = "Productos%20TCG"

FIELD_MAP = {
    "Name": "name",
    "Category": "category",
    "Price": "price",
    "Currency": "currency",
    "Status": "status",
    "Image URL": "image_url",
    "Description": "description",
    "Is Holo": "is_holo",
    "Set Name": "set_name",
    "Card Number": "card_number",
}


def transform_record(rec):
    fields = rec.get("fields", {})
    return {
        "id": int(hash(rec["id"]) % 100000) if "id" in rec else 0,
        "name": fields.get("Name", ""),
        "category": fields.get("Category", "singles"),
        "price": fields.get("Price", 0),
        "currency": fields.get("Currency", "MXN"),
        "status": fields.get("Status", "available"),
        "image_url": fields.get("Image URL", ""),
        "description": fields.get("Description", ""),
        "is_holo": fields.get("Is Holo", False),
        "set_name": fields.get("Set Name", ""),
        "card_number": fields.get("Card Number", ""),
    }


@app.get("/api/tcg-products")
async def get_products():
    async with httpx.AsyncClient(timeout=15) as client:
        all_records = []
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
        
        while url:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return JSONResponse(
                    {"error": "Airtable error", "detail": resp.text},
                    status_code=502,
                )
            data = resp.json()
            all_records.extend(data.get("records", []))
            offset = data.get("offset")
            url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}?offset={offset}" if offset else None
        
        products = [transform_record(r) for r in all_records]
        return {"products": products, "count": len(products)}


@app.get("/health")
async def health():
    return {"status": "ok"}
