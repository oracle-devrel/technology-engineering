from unittest.mock import MagicMock, patch

import pytest

from core.models import TranslateRequest
from core.translator import _build_chat_detail, _cached_system_prompt, translate_sync


@pytest.fixture(autouse=True)
def mock_glossary(monkeypatch):
    monkeypatch.setattr(
        "core.prompt.get_glossary_for_pair",
        lambda source_language, target_language: {},
    )
    monkeypatch.setattr(
        "core.translator.get_glossary_for_pair",
        lambda source_language, target_language: {},
    )
    _cached_system_prompt.cache_clear()
    yield
    _cached_system_prompt.cache_clear()


class TestBuildChatDetail:
    def test_generic_format_for_llama(self):
        req = TranslateRequest(
            text="Hello",
            source_language="english",
            target_language="spanish-mx",
            model_id="meta.llama-3.3-70b-instruct",
        )
        detail = _build_chat_detail(req)
        assert detail.chat_request.api_format == "GENERIC"
        assert detail.chat_request.messages is not None
        assert len(detail.chat_request.messages) == 2

    def test_cohere_format(self):
        req = TranslateRequest(
            text="Hello",
            source_language="english",
            target_language="portuguese-br",
            model_id="cohere.command-r-plus-08-2024",
        )
        detail = _build_chat_detail(req)
        assert detail.chat_request.api_format == "COHERE"
        assert detail.chat_request.message is not None

    def test_stream_flag(self):
        req = TranslateRequest(
            text="Hello",
            source_language="english",
            target_language="german",
        )
        detail = _build_chat_detail(req, stream=True)
        assert detail.chat_request.is_stream is True

    def test_non_english_pair(self):
        req = TranslateRequest(
            text="Hallo Welt",
            source_language="german",
            target_language="polish",
        )
        detail = _build_chat_detail(req)
        assert detail.chat_request.api_format == "COHEREV2"

    def test_cohere_command_a_uses_coherev2_format(self):
        req = TranslateRequest(
            text="Hello",
            source_language="english",
            target_language="swedish",
            model_id="cohere.command-a-03-2025",
        )
        detail = _build_chat_detail(req)
        assert detail.chat_request.api_format == "COHEREV2"
        assert detail.chat_request.messages is not None
        assert len(detail.chat_request.messages) == 2


class TestTranslateSync:
    @patch("core.translator._get_client")
    def test_sync_returns_response_coherev2(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_content = MagicMock(text="Hola mundo")
        mock_content.text = "Hola mundo"
        mock_result = MagicMock()
        mock_result.data.chat_response.message.content = [mock_content]
        mock_client.chat.return_value = mock_result

        req = TranslateRequest(
            text="Hello world",
            source_language="english",
            target_language="spanish-mx",
        )
        result = translate_sync(req)
        assert result.translated_text == "Hola mundo"
        assert result.source_language == "english"
        assert result.target_language == "spanish-mx"
        assert result.latency_ms > 0

    @patch("core.translator._get_client")
    def test_sync_returns_response_generic(self, mock_get_client, monkeypatch):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.data.chat_response.choices = [
            MagicMock(message=MagicMock(content=[MagicMock(text="bote")]))
        ]
        mock_client.chat.return_value = mock_result
        monkeypatch.setattr(
            "core.prompt.get_glossary_for_pair",
            lambda source_language, target_language: {"jackpot": "bote"},
        )

        req = TranslateRequest(
            text="win the jackpot",
            source_language="english",
            target_language="spanish-mx",
            model_id="meta.llama-3.3-70b-instruct",
        )
        result = translate_sync(req)
        assert result.translated_text == "bote"

        chat_detail = mock_client.chat.call_args.args[0]
        system_prompt = chat_detail.chat_request.messages[0].content[0].text
        assert "jackpot" in system_prompt
        assert "bote" in system_prompt

    @patch("core.translator._get_client")
    def test_sync_returns_exact_glossary_match_without_genai(
        self, mock_get_client, monkeypatch
    ):
        monkeypatch.setattr(
            "core.translator.get_glossary_for_pair",
            lambda source_language, target_language: {"jackpot": "bote"},
        )

        req = TranslateRequest(
            text="jackpot",
            source_language="english",
            target_language="spanish-mx",
        )
        result = translate_sync(req)

        assert result.translated_text == "bote"
        mock_get_client.assert_not_called()
