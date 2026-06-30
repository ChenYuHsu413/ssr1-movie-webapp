"""SQLite storage for the scraped movies (movie.db).

Run `python db.py` to (re)build movie.db from movies.csv.
"""
import csv
import sqlite3

DB_FILE = "movie.db"
CSV_FILE = "movies.csv"

# movies table column order (id first)
COLUMNS = ["id", "title", "categories", "regions", "minutes",
           "release_date", "score", "rating", "detail_url", "cover_url"]


def save_movies(movies, path=DB_FILE):
    """Create movie.db and write the given movie dicts (1-based id)."""
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE IF EXISTS movies")
    conn.execute(
        "CREATE TABLE movies (id INTEGER PRIMARY KEY, title TEXT, categories TEXT, "
        "regions TEXT, minutes TEXT, release_date TEXT, score TEXT, rating TEXT, "
        "detail_url TEXT, cover_url TEXT)"
    )
    rows = [
        tuple((m.get("id") or i) if c == "id" else m.get(c, "") for c in COLUMNS)
        for i, m in enumerate(movies, 1)
    ]
    placeholders = ",".join("?" * len(COLUMNS))
    conn.executemany(
        f"INSERT INTO movies ({','.join(COLUMNS)}) VALUES ({placeholders})", rows
    )
    conn.commit()
    conn.close()


def load_movies(path=DB_FILE):
    """Return all movies from movie.db as a list of dicts ordered by id."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT {','.join(COLUMNS)} FROM movies ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def from_csv(csv_path=CSV_FILE, path=DB_FILE):
    """Build movie.db from an existing movies.csv. Returns the row count."""
    with open(csv_path, encoding="utf-8-sig") as f:
        movies = list(csv.DictReader(f))
    for m in movies:
        m["id"] = int(m.pop("rank", 0) or 0)  # csv "rank" column becomes the id
    save_movies(movies, path)
    return len(movies)


if __name__ == "__main__":
    n = from_csv()
    print(f"Wrote {n} movies to {DB_FILE}")
