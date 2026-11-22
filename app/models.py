from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "serial_number BETWEEN 100000 AND 999999",
            name="ck_books_serial_number",
        ),
        CheckConstraint(
            "borrower_card_number BETWEEN 100000 AND 999999",
            name="ck_books_borrower_card_number",
        ),
        CheckConstraint(
            "(borrower_card_number IS NULL) = (borrowed_at IS NULL)",
            name="ck_books_complete_loan",
        ),
    )

    serial_number: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    borrower_card_number: Mapped[int | None]
    borrowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def is_borrowed(self) -> bool:
        return self.borrowed_at is not None
