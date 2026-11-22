import pytest

BOOK = {"serial_number": 123456, "title": "Solaris", "author": "Stanisław Lem"}


def test_list_starts_empty(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json() == []


def test_create_book_trims_text_and_starts_available(client):
    response = client.post("/books", json={**BOOK, "title": "  Solaris \t"})

    assert response.status_code == 201
    assert response.json() == {
        **BOOK,
        "is_borrowed": False,
        "borrower_card_number": None,
        "borrowed_at": None,
    }
    assert client.get("/books").json() == [response.json()]


def test_list_orders_copies_by_serial_number(client):
    for serial_number in (999999, 100000):
        response = client.post("/books", json={**BOOK, "serial_number": serial_number})
        assert response.status_code == 201

    books = client.get("/books").json()
    assert [book["serial_number"] for book in books] == [100000, 999999]


def test_duplicate_serial_number_leaves_original_book_unchanged(client):
    original = client.post("/books", json=BOOK)
    assert original.status_code == 201

    duplicate = client.post("/books", json={**BOOK, "title": "Eden"})

    assert duplicate.status_code == 409
    assert client.get("/books").json() == [original.json()]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("serial_number", 99999),
        ("serial_number", 1000000),
        ("serial_number", "123456"),
        ("serial_number", 123456.5),
        ("title", " \t"),
        ("author", ""),
    ],
)
def test_invalid_book_returns_422(client, field, value):
    response = client.post("/books", json={**BOOK, field: value})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]
