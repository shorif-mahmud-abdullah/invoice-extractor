import json

import pytest
from pydantic import ValidationError

from app.extractors.llm import LLMExtractor

VALID = {
    "invoice_number": "INV-9",
    "invoice_date": "2026-03-01",
    "vendor_name": "Acme",
    "line_items": [{"description": "Bolts", "quantity": 4, "unit_price": 2.5, "amount": 10}],
    "subtotal": 10,
    "tax": 1,
    "total": 11,
}


def test_valid_json_is_parsed_into_an_invoice():
    extractor = LLMExtractor(generate=lambda prompt: json.dumps(VALID))
    invoice = extractor.extract("some invoice text")
    assert invoice.invoice_number == "INV-9"
    assert invoice.line_items[0].description == "Bolts"


def test_json_wrapped_in_a_code_fence_is_accepted():
    fenced = "```json\n" + json.dumps(VALID) + "\n```"
    invoice = LLMExtractor(generate=lambda prompt: fenced).extract("text")
    assert invoice.total == 11


def test_prompt_includes_the_invoice_text():
    seen = {}

    def fake(prompt):
        seen["prompt"] = prompt
        return json.dumps(VALID)

    LLMExtractor(generate=fake).extract("UNIQUE-MARKER-123")
    assert "UNIQUE-MARKER-123" in seen["prompt"]


def test_model_output_that_breaks_the_schema_is_rejected():
    bad = dict(VALID, line_items=[{"description": "x", "quantity": -1, "unit_price": 1, "amount": 1}])
    with pytest.raises(ValidationError):
        LLMExtractor(generate=lambda prompt: json.dumps(bad)).extract("text")


def test_non_json_output_raises():
    with pytest.raises(json.JSONDecodeError):
        LLMExtractor(generate=lambda prompt: "sorry, I cannot do that").extract("text")
