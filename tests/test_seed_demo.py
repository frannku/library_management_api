from app.seed_demo import seed_demo


def test_seed_demo_preserves_edits_and_restores_missing_copy(test_engine, client):
    with test_engine.begin() as connection:
        assert seed_demo(connection) == 105
        assert seed_demo(connection) == 0

    books = client.get("/books").json()
    assert len(books) == 105
    assert sum(book["is_borrowed"] for book in books) == 25
    assert client.delete("/books/800001/loan").status_code == 204
    assert client.delete("/books/800003").status_code == 204

    with test_engine.begin() as connection:
        assert seed_demo(connection) == 1

    books[0]["is_borrowed"] = False
    books[0]["borrower_card_number"] = None
    books[0]["borrowed_at"] = None
    assert client.get("/books").json() == books
