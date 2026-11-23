# Library management API

Uruchom aplikację i bazę PostgreSQL z katalogu projektu.

```sh
docker compose up
```

Panel pracownika jest dostępny pod `http://localhost:8000/`.
Interaktywna dokumentacja API jest dostępna pod `http://localhost:8000/docs`.
Po zmianie kodu użyj `docker compose up --build`, żeby zbudować nowy obraz.

## Dane demonstracyjne

Po uruchomieniu aplikacji otwórz drugi terminal w katalogu projektu i wykonaj:

```sh
docker compose exec app python -m app.seed_demo
```

W pustym katalogu skrypt utworzy 105 egzemplarzy (21 tytułów po 5 kopii), w tym
80 dostępnych i 25 wypożyczonych. Numery seryjne obejmują zakres 800001–800105.
Skrypt pomija zajęte numery. Możesz go uruchomić ponownie po ręcznym zwrocie
lub wypożyczeniu. Jeśli usuniesz egzemplarz demo, następne uruchomienie go odtworzy.

### Wypróbuj katalog

1. Otwórz [panel pracownika](http://localhost:8000/). Przy samych danych demo
   na piątej stronie zobaczysz ostatnie pięć egzemplarzy.
2. Wyszukaj `Mapa deszczu`. W początkowym zbiorze dwie kopie są wypożyczone,
   a trzy dostępne.
3. Wypożycz egzemplarz `800003` na kartę `654321`. Sprawdź numer karty i datę
   w tabeli, a następnie kliknij „Zwróć”. Egzemplarz ponownie będzie dostępny.

## Książki

Przycisk „Pobierz wyniki CSV” eksportuje wszystkie egzemplarze pasujące do
aktywnego wyszukiwania. Pusty filtr obejmuje cały katalog. Przed zapisaniem
pliku panel podaje liczbę egzemplarzy i rozmiar w bajtach.

- `GET /books` zwraca egzemplarze według numeru seryjnego.
  Opcjonalne `q` wyszukuje fragment tytułu lub autora oraz dokładny numer seryjny.
  `limit` (1–100) i `offset` (od 0) pozwalają pobrać część wyników, np.
  `GET /books?q=solaris&limit=26&offset=0`. Panel pokazuje 25 egzemplarzy na stronę.
- `DELETE /books/{serial_number}` usuwa dostępny lub wypożyczony egzemplarz. Zwraca
  `204 No Content` po usunięciu albo `404 Not Found`, jeśli egzemplarz nie istnieje.
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

## Wypożyczenia

- `POST /books/{serial_number}/loan` wypożycza egzemplarz. Przykładowe dane to
  `{"borrower_card_number": 654321}`. API zapisuje bieżący czas w UTC, a próba
  wypożyczenia już wypożyczonej książki zwraca `409 Conflict`.
- `DELETE /books/{serial_number}/loan` oznacza egzemplarz jako dostępny i czyści
  dane wypożyczenia. Ponowny zwrot istniejącej książki również zwraca `204 No Content`.

Obie operacje zwracają `404 Not Found`, jeśli egzemplarz o podanym numerze nie istnieje.

## Testy

Komenda uruchamia `pytest` z PostgreSQL w osobnym projekcie Compose.

```sh
docker compose -p library-test run --rm --build test
docker compose -p library-test down
```
