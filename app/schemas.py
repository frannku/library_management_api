from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

SixDigitNumber = Annotated[int, Field(strict=True, ge=100_000, le=999_999)]


class BookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)

    serial_number: SixDigitNumber
    title: str
    author: str


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    serial_number: int
    title: str
    author: str
    is_borrowed: bool
    borrower_card_number: int | None
    borrowed_at: datetime | None
