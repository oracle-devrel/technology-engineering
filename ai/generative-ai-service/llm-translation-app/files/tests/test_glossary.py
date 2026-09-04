import pytest

from core import glossary


@pytest.fixture(autouse=True)
def reset_glossary_cache():
    old_glossary = glossary._glossary
    old_last_refresh_at = glossary._last_refresh_at
    try:
        glossary._glossary = {}
        glossary._last_refresh_at = 0.0
        yield
    finally:
        glossary._glossary = old_glossary
        glossary._last_refresh_at = old_last_refresh_at


def test_get_glossary_for_pair_loads_from_cache(monkeypatch):
    calls = 0

    def load_glossary():
        nonlocal calls
        calls += 1
        return {
            "jackpot": {
                "english": "jackpot",
                "spanish-mx": "bote",
            }
        }

    monkeypatch.setattr(glossary, "_load_glossary_from_bucket", load_glossary)

    assert glossary.get_glossary_for_pair("english", "spanish-mx") == {
        "jackpot": "bote"
    }
    assert glossary.get_glossary_for_pair("english", "spanish-mx") == {
        "jackpot": "bote"
    }
    assert calls == 1


def test_validate_glossary_rejects_invalid_shapes():
    with pytest.raises(ValueError):
        glossary._validate_glossary([])

    with pytest.raises(ValueError):
        glossary._validate_glossary({"jackpot": "bote"})

    with pytest.raises(ValueError):
        glossary._validate_glossary({"jackpot": {"english": 123}})


def test_missing_bucket_object_raises(monkeypatch):
    class NotFoundError(Exception):
        status = 404

    def load_glossary():
        raise NotFoundError()

    monkeypatch.setattr(glossary, "_load_glossary_from_bucket", load_glossary)

    with pytest.raises(glossary.GlossaryLoadError):
        glossary.get_glossary_for_pair("english", "spanish-mx")


def test_bucket_load_failure_raises(monkeypatch):
    def load_glossary():
        raise ValueError("bad bucket json")

    monkeypatch.setattr(glossary, "_load_glossary_from_bucket", load_glossary)

    with pytest.raises(glossary.GlossaryLoadError):
        glossary.get_glossary_for_pair("english", "spanish-mx")
