"""Extraction pipeline: text -> extractor -> validation -> result."""
import os

from app.extractors.llm import LLMExtractor
from app.extractors.rules import extract_with_rules
from app.schemas import ExtractionResult
from app.validation import validate_invoice


def process(text: str, mode: str = "auto", llm: LLMExtractor | None = None) -> ExtractionResult:
    """mode: 'rules', 'llm', or 'auto' (LLM when GEMINI_API_KEY is set, else rules)."""
    use_llm = mode == "llm" or (mode == "auto" and bool(os.getenv("GEMINI_API_KEY")))

    if use_llm:
        invoice = (llm or LLMExtractor()).extract(text)
        method = "llm"
    else:
        invoice = extract_with_rules(text)
        method = "rules"

    warnings = validate_invoice(invoice)
    return ExtractionResult(
        invoice=invoice, method=method, warnings=warnings, needs_review=bool(warnings)
    )
