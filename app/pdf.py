"""Turn an uploaded file into plain text."""
from io import BytesIO

from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return content.decode("utf-8", errors="replace")
