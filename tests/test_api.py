from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
client = TestClient(app)


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def upload(name, content, **params):
    return client.post("/extract", files={"file": (name, content)}, params=params)


def test_health():
    assert client.get("/health").json() == {"status": "healthy"}


def test_clean_invoice_is_extracted_without_warnings():
    response = upload("invoice_001.txt", (SAMPLES / "invoice_001.txt").read_bytes())
    body = response.json()
    assert response.status_code == 200
    assert body["method"] == "rules"
    assert body["needs_review"] is False
    assert body["warnings"] == []
    assert body["invoice"]["total"] == "1375.00"


def test_inconsistent_invoice_is_flagged_for_review():
    response = upload("invoice_003_with_error.txt", (SAMPLES / "invoice_003_with_error.txt").read_bytes())
    body = response.json()
    assert response.status_code == 200
    assert body["needs_review"] is True
    joined = " ".join(body["warnings"])
    assert "subtotal" in joined.lower()
    assert "Due date" in joined


def test_pdf_upload_is_supported():
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 800
    for line in (SAMPLES / "invoice_001.txt").read_text().splitlines():
        pdf.drawString(50, y, line)
        y -= 18
    pdf.save()

    response = upload("invoice.pdf", buffer.getvalue())
    body = response.json()
    assert response.status_code == 200
    assert body["invoice"]["invoice_number"] == "INV-2026-0042"
    assert body["needs_review"] is False


def test_empty_file_is_rejected():
    assert upload("empty.txt", b"   ").status_code == 422


def test_corrupt_pdf_is_rejected():
    assert upload("broken.pdf", b"not really a pdf").status_code == 422


def test_invalid_mode_is_rejected():
    response = upload("invoice_001.txt", b"x", mode="magic")
    assert response.status_code == 422
