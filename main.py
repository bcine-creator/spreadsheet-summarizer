from openai import OpenAI
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import io
import openpyxl
from typing import Dict
import os
import openai

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SheetSummaries(BaseModel):
    summaries: Dict[str, str]

def convert_to_xlsx_url(google_url: str) -> str:
    if "/d/" in google_url:
        file_id = google_url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    raise ValueError("Invalid Google Sheets URL")

def summarize_text(text: str) -> str:
    prompt = f"Summarize the following spreadsheet tab content:\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

@app.get("/summarize", response_model=SheetSummaries)
def summarize_spreadsheet(url: str = Query(..., description="Public Google Sheets URL")):
    try:
        download_url = convert_to_xlsx_url(url)
        response = requests.get(download_url)
        response.raise_for_status()

        wb = openpyxl.load_workbook(io.BytesIO(response.content), data_only=True, keep_links=False)
        summaries = {}

        for sheet_name in wb.sheetnames:
            try:
                sheet = wb[sheet_name]
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    rows.append("\t".join([str(cell) if cell is not None else "" for cell in row]))
                sheet_text = "\n".join(rows)
                summary = summarize_text(sheet_text[:5000])
                summaries[sheet_name] = summary
            except Exception as e:
                print(f"❌ Skipping sheet '{sheet_name}' due to error: {e}")
                summaries[sheet_name] = f"Error reading this sheet: {str(e)}"

        return {"summaries": summaries}

    except Exception as e:
        print("❌ Error:", str(e))  # Shows up in Render logs
        return JSONResponse(status_code=500, content={"error": str(e)})
