"""LLM extractor using Google Gemini with JSON output validated by Pydantic.

The model call is injected (`generate`), so tests can run without network or a key.
"""
import json
import os
from typing import Callable, Optional

from app.schemas import Invoice

PROMPT = """You extract data from invoices. Return ONLY a JSON object with these keys:
invoice_number (string), invoice_date (YYYY-MM-DD), due_date (YYYY-MM-DD or null),
vendor_name (string), bill_to (string or null), currency (3-letter code or null),
line_items (list of objects with description, quantity, unit_price, amount),
subtotal (number or null), tax (number or null), total (number).
Use null for anything not present. Never invent values.

Invoice text:
---
{text}
---
"""


def _gemini_generate(prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash"))
    response = model.generate_content(
        prompt, generation_config={"response_mime_type": "application/json"}
    )
    return response.text


class LLMExtractor:
    def __init__(self, generate: Optional[Callable[[str], str]] = None):
        self.generate = generate or _gemini_generate

    def extract(self, text: str) -> Invoice:
        raw = self.generate(PROMPT.format(text=text))
        data = json.loads(_strip_code_fence(raw))
        return Invoice.model_validate(data)


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()
