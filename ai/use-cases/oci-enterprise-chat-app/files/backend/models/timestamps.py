"""Normalize legacy UTC timestamps that were stored without an offset."""

from datetime import UTC, datetime

from pydantic import BaseModel, field_validator


class TimestampModel(BaseModel):
    @field_validator("*", mode="after")
    @classmethod
    def normalize_timestamp(cls, value):
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
