{\rtf1\ansi\ansicpg1252\cocoartf2862
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import uvicorn\
from fastapi import FastAPI, Query\
from pydantic import BaseModel\
import requests\
import io\
import openpyxl\
from typing import Dict\
import os\
import openai\
\
app = FastAPI()\
\
openai.api_key = os.getenv("OPENAI_API_KEY")\
\
class SheetSummaries(BaseModel):\
    summaries: Dict[str, str]\
\
def convert_to_xlsx_url(google_url: str) -> str:\
    if "/d/" in google_url:\
        file_id = google_url.split("/d/")[1].split("/")[0]\
        return f"https://docs.google.com/spreadsheets/d/\{file_id\}/export?format=xlsx"\
    raise ValueError("Invalid Google Sheets URL")\
\
def summarize_text(text: str) -> str:\
    prompt = f"Summarize the following spreadsheet tab content:\\n\\n\{text\}"\
    response = openai.ChatCompletion.create(\
        model="gpt-4",\
        messages=[\{"role": "user", "content": prompt\}],\
        temperature=0.5\
    )\
    return response['choices'][0]['message']['content'].strip()\
\
@app.get("/summarize", response_model=SheetSummaries)\
def summarize_spreadsheet(url: str = Query(..., description="Public Google Sheets URL")):\
    try:\
        download_url = convert_to_xlsx_url(url)\
        response = requests.get(download_url)\
        response.raise_for_status()\
\
        wb = openpyxl.load_workbook(io.BytesIO(response.content), data_only=True)\
        summaries = \{\}\
\
        for sheet_name in wb.sheetnames:\
            sheet = wb[sheet_name]\
            rows = []\
            for row in sheet.iter_rows(values_only=True):\
                rows.append("\\t".join([str(cell) if cell is not None else "" for cell in row]))\
            sheet_text = "\\n".join(rows)\
            summary = summarize_text(sheet_text[:5000])  # Optional: truncate long tabs\
            summaries[sheet_name] = summary\
\
        return \{"summaries": summaries\}\
    except Exception as e:\
        return \{"error": str(e)\}\
}