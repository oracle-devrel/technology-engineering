from __future__ import annotations

from pydantic import BaseModel, field_validator

from core.config import ALLOWED_PAIRS, DEFAULT_MODEL, SUPPORTED_LANGUAGES


class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str
    model_id: str = DEFAULT_MODEL

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{v}'. Must be one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
            )
        return v

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v

    def model_post_init(self, __context: object) -> None:
        if self.source_language == self.target_language:
            raise ValueError("source_language and target_language must differ")
        pair = frozenset({self.source_language, self.target_language})
        if pair not in ALLOWED_PAIRS:
            raise ValueError(
                f"Language pair '{self.source_language}' → '{self.target_language}' is not supported"
            )


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    model_id: str
    latency_ms: float


