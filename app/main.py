from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_session
from .models import Book
from .schemas import BookCreate, BookRead

DatabaseSession = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        Base.metadata.create_all(engine)
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Library management API", lifespan=lifespan)


@app.get("/books", response_model=list[BookRead])
def list_books(session: DatabaseSession):
    return session.scalars(select(Book).order_by(Book.serial_number)).all()


@app.post(
    "/books",
    response_model=BookRead,
    status_code=201,
    responses={409: {"description": "Serial number already exists"}},
)
def create_book(book_data: BookCreate,
                session: DatabaseSession):
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
