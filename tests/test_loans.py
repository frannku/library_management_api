from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest

LOAN_URL = "/books/123456/loan"
CARD = {"borrower_card_number": 654321}


@pytest.fixture
def loan_url(client):
    response = client.post(
        "/books", json={"serial_number": 123456, "title": "Solaris", "author": "Lem"}
    )
    assert response.status_code == 201
    return LOAN_URL


def test_borrow_book_saves_card_and_current_utc_time(client, loan_url):
    before = datetime.now(timezone.utc)
    response = client.post(loan_url, json=CARD)
    after = datetime.now(timezone.utc)

    assert response.status_code == 200
    book = response.json()
    assert book["is_borrowed"] is True
    assert book["borrower_card_number"] == CARD["borrower_card_number"]
    borrowed_at = datetime.fromisoformat(book["borrowed_at"])
    assert borrowed_at.utcoffset() == timedelta(0)
    assert before <= borrowed_at <= after
    assert client.get("/books").json() == [book]


def test_already_borrowed_book_keeps_original_loan(client, loan_url):
    first = client.post(loan_url, json=CARD)
    assert first.status_code == 200

    second = client.post(loan_url, json={"borrower_card_number": 654322})

    assert second.status_code == 409
    assert client.get("/books").json() == [first.json()]


def test_only_one_concurrent_checkout_succeeds(client, loan_url):
    start = Barrier(2)

    def borrow(card_number):
        start.wait(timeout=5)
        return client.post(loan_url, json={"borrower_card_number": card_number})

    with ThreadPoolExecutor(max_workers=2) as workers:
        responses = list(workers.map(borrow, [654321, 654322]))

    success, conflict = sorted(responses, key=lambda response: response.status_code)
    assert success.status_code == 200
    assert conflict.status_code == 409
    assert client.get("/books").json() == [success.json()]


def test_borrow_missing_book_returns_404(client):
    assert client.post(LOAN_URL, json=CARD).status_code == 404


@pytest.mark.parametrize("card_number", [99999, 1000000, "654321"])
def test_borrow_with_invalid_card_returns_422(client, loan_url, card_number):
    response = client.post(loan_url, json={"borrower_card_number": card_number})

    assert response.status_code == 422


@pytest.mark.parametrize("serial_number", ["99999", "0123456", "123456.0"])
def test_borrow_with_invalid_serial_number_returns_422(client, serial_number):
    response = client.post(f"/books/{serial_number}/loan", json=CARD)

    assert response.status_code == 422


def test_return_book_clears_loan_fields(client, loan_url):
    assert client.post(loan_url, json=CARD).status_code == 200

    response = client.delete(loan_url)

    assert response.status_code == 204
    assert response.content == b""
    book = client.get("/books").json()[0]
    assert book["is_borrowed"] is False
    assert book["borrower_card_number"] is None
    assert book["borrowed_at"] is None
    assert client.delete(loan_url).status_code == 204
    assert client.post(loan_url, json=CARD).status_code == 200


def test_return_missing_book_returns_404(client):
    assert client.delete(LOAN_URL).status_code == 404
