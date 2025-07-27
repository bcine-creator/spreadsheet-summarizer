import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import requests
import csv
from typing import Dict

app = FastAPI()

def parse_csv_totals(content: bytes) -> dict:
    lines = content.decode("utf-8").splitlines()
    reader = csv.DictReader(lines)

    total_realized = 0.0
    total_unrealized = 0.0
    total_fees = 0.0
    trade_count = 0

    for row in reader:
        try:
            trade_count += 1
            total_realized += float(row.get("Realized P/L", 0) or 0)
            total_unrealized += float(row.get("Unrealized P/L", 0) or 0)
            total_fees += float(row.get("Fees", 0) or 0)
        except ValueError:
            continue  # skip rows with invalid numbers

    return {
        "number_of_trades": trade_count,
        "total_realized_PL": round(total_realized, 2),
        "total_unrealized_PL": round(total_unrealized, 2),
        "total_fees": round(total_fees, 2)
    }

@app.get("/totals")
def get_spreadsheet_totals(url: str = Query(..., description="Public CSV URL")):
    try:
        response = requests.get(url)
        response.raise_for_status()
        totals = parse_csv_totals(response.content)
        return {"totals": {"Options Trades 2025": totals}}
    except Exception as e:
        print("❌ Error:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
