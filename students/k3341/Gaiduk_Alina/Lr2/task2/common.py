from __future__ import annotations

import os
import sqlite3
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("LR2_TASK2_DB", BASE_DIR / "lr1_parsed_pages.db"))
DEFAULT_TIMEOUT = 10
DEFAULT_URLS = [
    "https://example.com/",
    "https://www.python.org/",
    "https://docs.python.org/3/",
    "https://peps.python.org/pep-0008/",
    "https://www.iana.org/domains/reserved",
    "https://www.wikipedia.org/",
]


class ParseError(RuntimeError):
    pass


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._parts.append(data)

    @property
    def title(self) -> str | None:
        title = " ".join(part.strip() for part in self._parts if part.strip())
        return " ".join(title.split()) or None


def extract_title(html: str) -> str:
    parser = TitleParser()
    parser.feed(html)

    if parser.title is None:
        raise ParseError("HTML page does not contain a <title> tag")

    return parser.title


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LR2Parser/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_charset() or "utf-8"
            body = response.read()
    except HTTPError as error:
        raise ParseError(f"HTTP error {error.code} for {url}") from error
    except URLError as error:
        raise ParseError(f"Network error for {url}: {error.reason}") from error
    except TimeoutError as error:
        raise ParseError(f"Timeout while loading {url}") from error

    return body.decode(content_type, errors="replace")


def chunked(items: list[str], parts: int) -> list[list[str]]:
    if parts < 1:
        raise ValueError("workers must be greater than zero")

    chunk_count = min(parts, len(items))
    chunk_size, remainder = divmod(len(items), chunk_count)
    chunks = []
    current = 0

    for index in range(chunk_count):
        current_size = chunk_size + (1 if index < remainder else 0)
        chunks.append(items[current : current + current_size])
        current += current_size

    return chunks


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (name, owner_id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'medium',
                deadline TEXT,
                estimated_minutes INTEGER,
                owner_id INTEGER NOT NULL,
                category_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS parsed_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                approach TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                parsed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                UNIQUE (url, approach)
            );
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO users (email, full_name, hashed_password)
            VALUES ('parser@example.local', 'LR2 Parser', 'not-used')
            """
        )
        owner_id = get_owner_id(connection)
        connection.execute(
            """
            INSERT OR IGNORE INTO categories (name, owner_id)
            VALUES ('Parsed pages', ?)
            """,
            (owner_id,),
        )


def get_owner_id(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT id FROM users WHERE email = 'parser@example.local'"
    ).fetchone()
    if row is None:
        raise RuntimeError("Parser user was not created")
    return int(row[0])


def get_category_id(connection: sqlite3.Connection, owner_id: int) -> int:
    row = connection.execute(
        "SELECT id FROM categories WHERE name = 'Parsed pages' AND owner_id = ?",
        (owner_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Parsed pages category was not created")
    return int(row[0])


def save_page_title(url: str, title: str, approach: str) -> int:
    description = f"Source URL: {url}\nParsed by: {approach}"

    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")

        owner_id = get_owner_id(connection)
        category_id = get_category_id(connection, owner_id)

        existing = connection.execute(
            """
            SELECT task_id
            FROM parsed_pages
            WHERE url = ? AND approach = ?
            """,
            (url, approach),
        ).fetchone()

        if existing is not None:
            task_id = int(existing[0])
            connection.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, description, task_id),
            )
            return task_id

        cursor = connection.execute(
            """
            INSERT INTO tasks (title, description, status, priority, owner_id, category_id)
            VALUES (?, ?, 'todo', 'medium', ?, ?)
            """,
            (title, description, owner_id, category_id),
        )
        task_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT INTO parsed_pages (url, approach, task_id)
            VALUES (?, ?, ?)
            """,
            (url, approach, task_id),
        )
        return task_id


def parse_urls_argument(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_URLS

    urls = [url.strip() for url in value.split(",") if url.strip()]
    if not urls:
        raise ValueError("URL list must contain at least one URL")
    return urls
