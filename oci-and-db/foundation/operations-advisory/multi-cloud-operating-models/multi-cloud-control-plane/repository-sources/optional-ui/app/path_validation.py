"""Validation helpers for paths used by GitOps writes."""
import re


_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_path_segment(value: str, field_name: str) -> str:
    """Return a safe single path segment or raise ``ValueError``."""
    if (
        not isinstance(value, str)
        or not value
        or value == "."
        or ".." in value
        or not _SAFE_SEGMENT.fullmatch(value)
    ):
        raise ValueError(f"Invalid {field_name}")
    return value


def validate_relative_path(value: str, field_name: str = "resource path") -> str:
    """Return a safe slash-delimited relative path or raise ``ValueError``."""
    if not isinstance(value, str) or not value or value.startswith("/") or value.endswith("/"):
        raise ValueError(f"Invalid {field_name}")

    segments = value.split("/")
    if any(not segment for segment in segments):
        raise ValueError(f"Invalid {field_name}")
    for segment in segments:
        validate_path_segment(segment, field_name)
    return value
