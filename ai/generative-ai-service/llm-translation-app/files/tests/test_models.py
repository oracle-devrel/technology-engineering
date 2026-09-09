import pytest
from pydantic import ValidationError

from core.models import TranslateRequest, TranslateResponse


class TestTranslateRequest:
    def test_valid_request(self):
        req = TranslateRequest(
            text="Hello world",
            source_language="english",
            target_language="spanish-mx",
        )
        assert req.source_language == "english"
        assert req.target_language == "spanish-mx"
        assert req.model_id == "cohere.command-a-03-2025"

    def test_custom_model(self):
        req = TranslateRequest(
            text="Hello",
            source_language="english",
            target_language="german",
            model_id="cohere.command-r-plus-08-2024",
        )
        assert req.model_id == "cohere.command-r-plus-08-2024"

    def test_case_insensitive_language(self):
        req = TranslateRequest(
            text="Hello",
            source_language="English",
            target_language="GERMAN",
        )
        assert req.source_language == "english"
        assert req.target_language == "german"

    def test_unsupported_language(self):
        with pytest.raises(ValidationError, match="Unsupported language"):
            TranslateRequest(
                text="Hello",
                source_language="english",
                target_language="japanese",
            )

    # Every allowed pair tested in both directions
    @pytest.mark.parametrize(
        "source, target",
        [
            # English ↔ …
            ("english", "german"),
            ("german", "english"),
            ("english", "spanish-mx"),
            ("spanish-mx", "english"),
            ("english", "polish"),
            ("polish", "english"),
            ("english", "portuguese-br"),
            ("portuguese-br", "english"),
            ("english", "swedish"),
            ("swedish", "english"),
            # German ↔ …
            ("german", "polish"),
            ("polish", "german"),
            ("german", "swedish"),
            ("swedish", "german"),
            ("german", "spanish-mx"),
            ("spanish-mx", "german"),
            ("german", "portuguese-br"),
            ("portuguese-br", "german"),
            # Spanish ↔ …
            ("spanish-mx", "polish"),
            ("polish", "spanish-mx"),
            ("spanish-mx", "swedish"),
            ("swedish", "spanish-mx"),
        ],
    )
    def test_valid_language_pair(self, source, target):
        req = TranslateRequest(text="test", source_language=source, target_language=target)
        assert req.source_language == source
        assert req.target_language == target

    @pytest.mark.parametrize(
        "source, target",
        [
            ("polish", "portuguese-br"),
            ("polish", "swedish"),
            ("portuguese-br", "swedish"),
            ("portuguese-br", "polish"),
            ("swedish", "polish"),
            ("swedish", "portuguese-br"),
            ("portuguese-br", "spanish-mx"),
            ("spanish-mx", "portuguese-br"),
        ],
    )
    def test_invalid_language_pair_raises(self, source, target):
        with pytest.raises(ValidationError, match="not supported"):
            TranslateRequest(text="test", source_language=source, target_language=target)

    def test_same_language_raises(self):
        with pytest.raises(ValidationError, match="must differ"):
            TranslateRequest(
                text="Hello",
                source_language="english",
                target_language="english",
            )

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            TranslateRequest(
                text="   ",
                source_language="english",
                target_language="german",
            )


class TestTranslateResponse:
    def test_response_fields(self):
        resp = TranslateResponse(
            translated_text="Hola mundo",
            source_language="english",
            target_language="spanish-mx",
            model_id="cohere.command-a-03-2025",
            latency_ms=123.45,
        )
        assert resp.translated_text == "Hola mundo"
        assert resp.latency_ms == 123.45
