# Library management API

Uruchom aplikację i bazę PostgreSQL z katalogu projektu.

```sh
docker compose up
```

Interaktywna dokumentacja API jest dostępna pod `http://localhost:8000/docs`.
Po zmianie kodu użyj `docker compose up --build`, żeby zbudować nowy obraz.

## Książki

- `GET /books` zwraca egzemplarze według numeru seryjnego.
- `POST /books` dodaje dostępny egzemplarz. W Swagger UI użyj przykładowego JSON-a poniżej.

```json
{
  "serial_number": 123456,
  "title": "Solaris",
  "author": "Stanisław Lem"
}
```

Ponowne użycie numeru seryjnego zwraca `409 Conflict`. Poprawne numery to liczby
całkowite od `100000` do `999999`.

## Testy

Komenda uruchamia `pytest` z PostgreSQL w osobnym projekcie Compose.

```sh
docker compose -p library-test run --rm --build test
docker compose -p library-test down
```
