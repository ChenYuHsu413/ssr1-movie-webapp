# ssr1 Movies

A small end-to-end project that scrapes the 100 movies from
[ssr1.scrape.center](https://ssr1.scrape.center/), stores them in a SQLite
database, and serves a **FastAPI** website with a poster grid, live search,
category filters, and an AI chatbot over the catalog.

**🎬 Live demo:** https://ssr1-movie-webapp-chenyu.streamlit.app/
(the Streamlit version — see [`streamlit_app.py`](streamlit_app.py))

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
| `streamlit_app.py` | Streamlit UI (deployed on Streamlit Community Cloud) |
| `MOVIES.md` | Generated Markdown table of all movies with posters |
| `DEPLOY.md` | Hosting instructions (Render / Railway / Hugging Face) |

## Deployment

There are two front-ends sharing the same `db.py` and `chatbot.py`:

- **Streamlit** (`streamlit_app.py`) — live at
  https://ssr1-movie-webapp-chenyu.streamlit.app/. Deploy on
  [Streamlit Community Cloud](https://share.streamlit.io): set the main file to
  `streamlit_app.py`. API keys go in the app's **Secrets** (TOML).
- **FastAPI** (`app.py`) — a standard ASGI app with a richer custom UI and a JSON
  API. Set the start command to `uvicorn app:app --host 0.0.0.0 --port $PORT`;
  Render's free web service is the simplest target. See [`DEPLOY.md`](DEPLOY.md).
  (Note: FastAPI does **not** run on Streamlit Cloud — that's what the Streamlit
  version is for.)
