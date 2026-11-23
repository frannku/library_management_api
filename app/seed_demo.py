from datetime import datetime, timedelta, timezone

from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert

from .database import engine
from .models import Book


TITLES = [
    ("Mapa deszczu", "Anna Wierzbowa"),
    ("Listy znad rzeki", "Jan Wolski"),
    ("Ogród na dachu", "Ewa Polna"),
    ("Nocny tramwaj", "Adam Rudnicki"),
    ("Atlas ciszy", "Maria Brzeg"),
    ("Dom przy torach", "Jan Wolski"),
    ("Powrót do portu", "Anna Wierzbowa"),
    ("Ślady na śniegu", "Iga Zaleska"),
    ("Siódmy peron", "Adam Rudnicki"),
    ("Zielony notes", "Ewa Polna"),
    ("Za linią lasu", "Iga Zaleska"),
    ("Rok nad jeziorem", "Maria Brzeg"),
    ("Dwie latarnie", "Piotr Lipowy"),
    ("Kronika podwórka", "Ola Dolna"),
    ("Puste nabrzeże", "Piotr Lipowy"),
    ("Muzyka schodów", "Ola Dolna"),
    ("Zimowy rozkład", "Jan Wolski"),
    ("W drodze na targ", "Anna Wierzbowa"),
    ("Pracownia zegarów", "Ewa Polna"),
    ("Kamienny most", "Iga Zaleska"),
    ("Ostatni prom", "Maria Brzeg"),
]


def seed_demo(connection: Connection) -> int:
    rows = []
    now = datetime.now(timezone.utc)
    for title_index, (title, author) in enumerate(TITLES):
        for copy_index in range(5):
            serial = 800001 + 5 * title_index + copy_index
            # One loan per title, plus a second loan for the first four titles.
            borrowed = copy_index == 0 or (title_index < 4 and copy_index == 1)
            rows.append({
                "serial_number": serial,
                "title": title,
                "author": author,
                "borrower_card_number": serial - 100000 if borrowed else None,
                "borrowed_at": now - timedelta(days=title_index + 1) if borrowed else None,
            })

    statement = insert(Book).values(rows).on_conflict_do_nothing(
        index_elements=[Book.serial_number]
    ).returning(Book.serial_number)
    return len(connection.execute(statement).scalars().all())


if __name__ == "__main__":
    with engine.begin() as connection:
        added = seed_demo(connection)
    print(f"Dodano egzemplarzy: {added}")
