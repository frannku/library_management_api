const form = document.querySelector("#add-book");
const rows = document.querySelector("#books");
const message = document.querySelector("#message");
const search = document.querySelector("#search");
const previous = document.querySelector("#previous");
const next = document.querySelector("#next");
const pageSize = 25;
let currentPage = 1;
let currentQuery = "";
let latestRequest = 0;

async function request(url, method = "GET", data) {
  const options = { method };
  if (data !== undefined) {
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json();
    const detail = Array.isArray(error.detail)
      ? error.detail.map(item => item.msg).join(", ")
      : error.detail;
    throw new Error(detail || response.statusText);
  }
  if (response.status !== 204) return response.json();
}

async function refresh(page = currentPage, query = currentQuery) {
  const requestId = ++latestRequest;
  // One extra book tells us whether to enable the Next button.
  const params = new URLSearchParams({ q: query, limit: pageSize + 1, offset: (page - 1) * pageSize });
  let books;
  try {
    books = await request("/books?" + params);
  } catch (error) {
    if (requestId === latestRequest) message.textContent = error.message;
    return;
  }
  if (requestId !== latestRequest) return;
  if (!books.length && page > 1) return refresh(page - 1, query);
  currentPage = page;
  currentQuery = query;
  rows.replaceChildren();
  for (const book of books.slice(0, pageSize)) showBook(book);
  const empty = document.querySelector("#empty");
  empty.textContent = query ? "Brak pasujących książek" : "Katalog jest pusty.";
  empty.hidden = books.length !== 0;
  document.querySelector("#page").textContent = "Strona " + page;
  previous.disabled = page === 1;
  next.disabled = books.length <= pageSize;
}

search.onsubmit = event => {
  event.preventDefault();
  message.textContent = "";
  refresh(1, search.elements.q.value.trim());
};
previous.onclick = () => refresh(currentPage - 1);
next.onclick = () => refresh(currentPage + 1);

function csvCell(value) {
  let text = String(value ?? "");
  // Keep titles and author names that resemble spreadsheet formulas as text.
  if (typeof value === "string" && /^\s*[=+@-]/.test(text)) text = "'" + text;
  return '"' + text.replaceAll('"', '""') + '"';
}

const exportButton = document.querySelector("#export");
exportButton.onclick = async () => {
  exportButton.disabled = true;
  message.textContent = "";
  try {
    const books = await request("/books?" + new URLSearchParams({ q: currentQuery }));
    const lines = ["Numer seryjny;Tytuł;Autor;Status;Numer karty;Wypożyczono (UTC)"];
    for (const book of books) {
      const cells = [book.serial_number, book.title, book.author,
        book.is_borrowed ? "Wypożyczona" : "Dostępna", book.borrower_card_number, book.borrowed_at];
      lines.push(cells.map(csvCell).join(";"));
    }
    const file = new Blob(["\uFEFF", lines.join("\r\n"), "\r\n"], { type: "text/csv;charset=utf-8" });
    const size = file.size.toLocaleString("pl-PL");
    if (!window.confirm(`Liczba egzemplarzy: ${books.length}. Rozmiar CSV: ${size} B. Pobrać plik?`)) return;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(file);
    link.download = "katalog.csv";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  } catch (error) {
    message.textContent = error.message;
  } finally {
    exportButton.disabled = false;
  }
};

async function runAction(button, action) {
  button.disabled = true;
  message.textContent = "";
  try {
    await action();
    await refresh();
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function addButton(container, label, action) {
  const button = document.createElement("button");
  button.textContent = label;
  button.onclick = () => runAction(button, action);
  container.append(button);
  return button;
}

function addDetail(cell, text) {
  const detail = document.createElement("small");
  detail.textContent = text;
  cell.append(detail);
}

function showBook(book) {
  const row = rows.insertRow();
  row.insertCell().textContent = book.serial_number;
  const title = row.insertCell();
  title.textContent = book.title;
  addDetail(title, book.author);
  const status = row.insertCell();
  status.textContent = book.is_borrowed ? "Wypożyczona" : "Dostępna";
  const actions = document.createElement("div");
  actions.className = "actions";
  row.insertCell().append(actions);
  const url = "/books/" + book.serial_number;
  if (book.is_borrowed) {
    addDetail(status, "Karta " + book.borrower_card_number);
    addDetail(status, new Date(book.borrowed_at).toLocaleString("pl-PL"));
    addButton(actions, "Zwróć", () => request(url + "/loan", "DELETE"));
  } else {
    addButton(actions, "Wypożycz", () => {
      const card = window.prompt("Podaj sześciocyfrowy numer karty bibliotecznej");
      if (card === null) return;
      if (!/^[1-9][0-9]{5}$/.test(card)) throw new Error("Numer karty musi mieć sześć cyfr i zaczynać się od 1–9.");
      return request(url + "/loan", "POST", { borrower_card_number: Number(card) });
    });
  }
  addButton(actions, "Usuń", () => {
    if (book.is_borrowed && !window.confirm("Egzemplarz jest wypożyczony. Czy na pewno go usunąć?")) return;
    return request(url, "DELETE");
  }).className = "remove";
}

form.onsubmit = event => {
  event.preventDefault();
  runAction(event.submitter, async () => {
    const fields = new FormData(form);
    await request("/books", "POST", {
      serial_number: Number(fields.get("serial")),
      title: fields.get("title"),
      author: fields.get("author"),
    });
    form.reset();
  });
};

refresh().catch(error => { message.textContent = error.message; });
