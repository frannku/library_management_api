from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path as FilePath

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg.errors import UniqueViolation
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_session
from .models import Book
from .schemas import BookCreate, BookRead, LoanCreate

def parse_serial_number(
    serial_number: str = Path(pattern=r"^[1-9][0-9]{5}$"),
) -> int:
    return int(serial_number)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        Base.metadata.create_all(engine)
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Library management API", lifespan=lifespan)
static_dir = FilePath(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def staff_panel() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/books", response_model=list[BookRead])
def list_books(
    q: str = "",
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> Sequence[Book]:
    statement = select(Book)
    term = q.strip()
    if term:
        matches = [
            Book.title.icontains(term, autoescape=True),
            Book.author.icontains(term, autoescape=True),
        ]
        if len(term) == 6 and term.isascii() and term.isdigit():
            matches.append(Book.serial_number == int(term))
        statement = statement.where(or_(*matches))
    statement = statement.order_by(Book.serial_number).offset(offset).limit(limit)
    return session.scalars(statement).all()


@app.post(
    "/books",
    response_model=BookRead,
    status_code=201,
    responses={409: {"description": "Serial number already exists"}},
)
def create_book(
    book_data: BookCreate,
    session: Session = Depends(get_session),
) -> Book:
    book = Book(
        serial_number=book_data.serial_number,
        title=book_data.title,
        author=book_data.author,
    )
    session.add(book)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if isinstance(error.orig, UniqueViolation):
            raise HTTPException(
                status_code=409, detail="Serial number already exists"
            ) from error
        raise

    return book


def get_book_for_update(serial_number: int, session: Session) -> Book:
    # A second checkout must wait until the first transaction finishes.
    book = session.get(Book, serial_number, with_for_update=True)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post(
    "/books/{serial_number}/loan",
    response_model=BookRead,
    responses={
        404: {"description": "Book not found"},
        409: {"description": "Book is already borrowed"},
    },
)
def borrow_book(
    loan_data: LoanCreate,
    serial_number: int = Depends(parse_serial_number),
    session: Session = Depends(get_session),
) -> Book:
    book = get_book_for_update(serial_number, session)
    if book.is_borrowed:
        raise HTTPException(status_code=409, detail="Book is already borrowed")

    book.borrower_card_number = loan_data.borrower_card_number
    book.borrowed_at = datetime.now(timezone.utc)
    session.commit()
    return book


@app.delete(
    "/books/{serial_number}/loan",
    status_code=204,
    response_class=Response,
    responses={404: {"description": "Book not found"}},
)
def return_book(
    serial_number: int = Depends(parse_serial_number),
    session: Session = Depends(get_session),
) -> None:
    book = get_book_for_update(serial_number, session)
    book.borrower_card_number = None
    book.borrowed_at = None
    session.commit()


@app.delete(
    "/books/{serial_number}",
    status_code=204,
    response_class=Response,
    responses={404: {"description": "Book not found"}},
)
def delete_book(
    serial_number: int = Depends(parse_serial_number),
    session: Session = Depends(get_session),
) -> None:
    book = get_book_for_update(serial_number, session)
    session.delete(book)
    session.commit()
