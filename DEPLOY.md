# Deploying the movie web app

The app is a FastAPI server (`app:app`). It loads movies from `movie.db` and
serves posters from `posters/` — both are committed, so **no scraping is needed
at runtime**. The chatbot is optional: with no API key it falls back to a local
keyword search, so the site works without any secrets.

Start command (all platforms):

```
uvicorn app:app --host 0.0.0.0 --port $PORT
```

`requirements.txt` lists the dependencies; `Procfile` declares the start command.

## Render (free web service) — easiest

1. Push this repo to GitHub (done).
2. On https://render.com → **New → Web Service** → connect this repo.
3. Settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. (Optional) Add environment variables for the chatbot:
   `GROQ_API_KEY`, or `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY`.
5. Deploy. Note: the free tier sleeps when idle (~30s cold start).

## Railway

1. https://railway.app → **New Project → Deploy from GitHub repo**.
2. It auto-detects Python and the `Procfile`.
3. Add the same optional API-key variables under **Variables**.

## Hugging Face Spaces (Docker)

Create a Space (SDK: Docker) with a `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

Set API keys under the Space's **Settings → Secrets**.

## Notes

- **Never commit `.env`** — it is git-ignored. Set keys in the platform's env/secret settings instead.
- If you delete `movie.db`, the app falls back to scraping `ssr1.scrape.center`
  on startup (whose TLS cert is expired, so this is best avoided in production).
- Python 3.12 or 3.13 is recommended on the host (some platforms don't yet
  support 3.14).
