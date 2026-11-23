from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

SixDigitNumber = Annotated[int, Field(strict=True, ge=100_000, le=999_999)]


class BookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)

    serial_number: SixDigitNumber
    title: str
    author: str


class LoanCreate(BaseModel):
    borrower_card_number: SixDigitNumber


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    serial_number: int
    title: str
    author: str
    is_borrowed: bool
    borrower_card_number: int | None
    borrowed_at: datetime | None

    @field_validator("borrowed_at")
    @classmethod
    def use_utc(cls, borrowed_at: datetime | None) -> datetime | None:
        if borrowed_at is None:
            return None
        return borrowed_at.astimezone(timezone.utc)
