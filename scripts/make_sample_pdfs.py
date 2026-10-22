"""Render the .txt samples as PDFs, to try the PDF upload path.

    pip install reportlab
    python scripts/make_sample_pdfs.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def render(txt_path: Path) -> Path:
    pdf_path = txt_path.with_suffix(".pdf")
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    y = 800
    for line in txt_path.read_text().splitlines():
        pdf.drawString(50, y, line)
        y -= 18
    pdf.save()
    return pdf_path


if __name__ == "__main__":
    for path in sorted(SAMPLES.glob("*.txt")):
        print("wrote", render(path))
