from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_API_KEY", "")
BASE_ID = "appCXMRLvsM7p6gtA"
TABLE = "Productos%20TCG"


def transform_record(rec):
    fields = rec.get("fields", {})
    return {
        "id": abs(hash(rec.get("id", ""))) % 100000,
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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/tcg-products":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                req = Request(
                    f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}?pageSize=100",
                    headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}"},
                )
                resp = urlopen(req, timeout=15)
                data = json.loads(resp.read().decode())

                all_records = data.get("records", [])

                # Handle pagination
                while data.get("offset"):
                    offset_url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}?offset={data['offset']}&pageSize=100"
                    req = Request(
                        offset_url,
                        headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}"},
                    )
                    resp = urlopen(req, timeout=15)
                    data = json.loads(resp.read().decode())
                    all_records.extend(data.get("records", []))

                products = [transform_record(r) for r in all_records]

                # Deduplicate
                seen = set()
                unique = []
                for p in products:
                    key = f"{p['name']}|{p['price']}|{p['currency']}"
                    if key not in seen:
                        seen.add(key)
                        unique.append(p)

                result = {"products": unique, "count": len(unique)}
                self.wfile.write(json.dumps(result).encode())

            except URLError as e:
                self.wfile.write(
                    json.dumps({"error": "Airtable error", "detail": str(e.reason)}).encode()
                )
            except Exception as e:
                self.wfile.write(
                    json.dumps({"error": str(e)}).encode()
                )
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode())
