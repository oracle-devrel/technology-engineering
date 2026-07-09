from dbman_opsi.oci_util import safe_lookup


def test_safe_lookup_retries_once_then_returns_value() -> None:
    calls = 0

    def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary")
        return "ok"

    assert safe_lookup(flaky, "default") == "ok"
    assert calls == 2


def test_safe_lookup_returns_default_after_attempts_exhausted() -> None:
    calls = 0

    def broken() -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("down")

    assert safe_lookup(broken, "default") == "default"
    assert calls == 2
