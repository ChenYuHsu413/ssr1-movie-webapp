# ssr1 Movies

A small end-to-end project that scrapes the 100 movies from
[ssr1.scrape.center](https://ssr1.scrape.center/), stores them in a SQLite
database, and serves a **FastAPI** website with a poster grid, live search,
category filters, and an AI chatbot over the catalog.

## Features

- **Scraper** (`crawler.py`) — pulls all 10 pages and extracts title, categories,
  region, runtime, release date, score, rating, detail link, and poster. Also
  downloads posters and exports `movies.csv`, `movies.xlsx` (with embedded
  posters), `MOVIES.md`, and `movie.db`.
- **SQLite catalog** (`db.py` → `movie.db`) — the app's data source, so no
  scraping happens at runtime.
- **FastAPI site** (`app.py`):
  - `GET /` — poster grid with a hero search bar and category filter chips
  - `GET /chat` — full-page chatbot, plus a floating chat widget on the grid
  - `GET /movies` and `GET /movies/{id}` — JSON API
  - `GET /posters/{id}.jpg` — poster images (static)
- **Chatbot** (`chatbot.py`) — answers questions about the catalog. Tries cloud
  providers in order **Groq → Gemini → Claude**, cascading on failure, and falls
  back to an offline keyword search if no key is set or all calls fail.

## Quick start

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Then open http://127.0.0.1:8000/.

The app loads from `movie.db` on startup. If `movie.db` is missing it scrapes the
site live and saves the DB for next time.

## Chatbot keys (optional)

The chatbot works with no key (local search). To enable a cloud provider, copy
`.env.example` to `.env` and set one of:

```
GROQ_API_KEY=...      # preferred
GEMINI_API_KEY=...    # or Google Gemini
ANTHROPIC_API_KEY=... # or Anthropic Claude
```

`.env` is git-ignored — never commit your keys.

## Re-scraping

```bash
python crawler.py   # refreshes posters/, movies.csv, movies.xlsx, MOVIES.md, movie.db
```

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | FastAPI web app (HTML grid + JSON API + chatbot routes) |
| `crawler.py` | Scraper and exporters (CSV / XLSX / Markdown / DB / posters) |
| `db.py` | SQLite read/write; `python db.py` rebuilds `movie.db` from `movies.csv` |
| `chatbot.py` | Catalog chatbot with provider cascade + local fallback |
| `movie.db` | SQLite catalog of 100 movies (the app's data source) |
| `posters/` | Downloaded poster thumbnails |
| `MOVIES.md` | Generated Markdown table of all movies with posters |
| `DEPLOY.md` | Hosting instructions (Render / Railway / Hugging Face) |

## Deployment

See [`DEPLOY.md`](DEPLOY.md). In short, it's a standard FastAPI app — set the
start command to `uvicorn app:app --host 0.0.0.0 --port $PORT`. Render's free web
service is the simplest target; `requirements.txt` and `Procfile` are included.

> Note: this is an ASGI server app, so it does **not** run on Streamlit
> Community Cloud as-is (that platform only hosts `streamlit run` apps).
