"""FastAPI app: upload an invoice, get validated structured data back."""
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from app.pdf import extract_text
from app.schemas import ExtractionResult
from app.service import process

app = FastAPI(
    title="Invoice Extractor",
    version="1.0.0",
    description="Turns invoice PDFs and text into validated, ERP-ready JSON.",
)

MAX_BYTES = 5 * 1024 * 1024


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/extract", response_model=ExtractionResult)
async def extract(
    file: UploadFile = File(..., description="Invoice as .pdf or .txt"),
    mode: str = Query("auto", pattern="^(auto|rules|llm)$"),
):
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 5 MB")

    try:
        text = extract_text(file.filename or "", content)
    except Exception as exc:  # unreadable or corrupt PDF
        raise HTTPException(status_code=422, detail=f"Could not read file: {exc}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text found. Scanned images need OCR.")

    try:
        return process(text, mode=mode)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}")
