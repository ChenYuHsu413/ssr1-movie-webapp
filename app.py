"""FastAPI app for the ssr1.scrape.center movies.

Loads movies from movie.db on startup (falls back to a live scrape if the DB is
missing), downloads posters into posters/, then serves:
  GET /              -> HTML grid of movies with posters
  GET /movies        -> JSON list of all movies
  GET /movies/{id}   -> JSON for one movie (id = 1..100)
  GET /posters/{id}.jpg -> poster image (static)
  GET /chat          -> HTML chat page
  POST /api/chat     -> {"reply": ...} chatbot answer about the movies

Run:  uvicorn app:app --reload
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # load API keys from a .env file before importing chatbot

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from crawler import crawl_all, ensure_posters, POSTER_DIR
from chatbot import answer
from db import load_movies, save_movies, DB_FILE

MOVIES = []  # filled on startup; each item gets an "id" (1-based)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(DB_FILE):
        print(f"Loading movies from {DB_FILE} ...")
        movies = load_movies()
    else:
        print(f"{DB_FILE} not found, scraping ssr1.scrape.center ...")
        movies = crawl_all()
        save_movies(movies)  # persist so the next boot is instant
    ensure_posters(movies)
    for i, m in enumerate(movies, 1):
        m.setdefault("id", i)
        m["poster"] = f"/posters/{m['id']}.jpg"
    MOVIES.extend(movies)
    print(f"Ready: {len(MOVIES)} movies loaded.")
    yield


app = FastAPI(title="ssr1 Movies", lifespan=lifespan)
app.mount("/posters", StaticFiles(directory=POSTER_DIR), name="posters")


@app.get("/movies")
def list_movies():
    return MOVIES


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    if 1 <= movie_id <= len(MOVIES):
        return MOVIES[movie_id - 1]
    raise HTTPException(status_code=404, detail="Movie not found")


class ChatIn(BaseModel):
    message: str


@app.post("/api/chat")
def chat(body: ChatIn):
    return {"reply": answer(body.message, MOVIES)}


@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Movie Chatbot</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #f5f5f5;
            display: flex; flex-direction: column; height: 100vh; }}
    header {{ background: #1f2d3d; color: #fff; padding: 16px 24px; }}
    header a {{ color: #9ecbff; }}
    #log {{ flex: 1; overflow-y: auto; padding: 24px; }}
    .msg {{ max-width: 70%; padding: 10px 14px; border-radius: 12px; margin: 8px 0;
            white-space: pre-wrap; line-height: 1.4; }}
    .user {{ background: #409eff; color: #fff; margin-left: auto; }}
    .bot {{ background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.12); }}
    form {{ display: flex; gap: 8px; padding: 16px 24px; background: #fff;
            border-top: 1px solid #e0e0e0; }}
    input {{ flex: 1; padding: 10px 14px; border: 1px solid #ccc; border-radius: 8px;
             font-size: 15px; }}
    button {{ padding: 10px 20px; border: 0; border-radius: 8px; background: #409eff;
              color: #fff; font-size: 15px; cursor: pointer; }}
  </style>
</head>
<body>
  <header><h1>🎬 Movie Chatbot</h1><a href="/">← back to grid</a></header>
  <div id="log"></div>
  <form id="f">
    <input id="m" placeholder="问我关于电影的问题，例如：评分最高的电影" autocomplete="off" autofocus>
    <button>发送</button>
  </form>
  <script>
    const log = document.getElementById('log');
    function add(text, who) {{
      const d = document.createElement('div');
      d.className = 'msg ' + who;
      d.textContent = text;
      log.appendChild(d);
      log.scrollTop = log.scrollHeight;
    }}
    add('你好！输入 “帮助” 看看我能做什么。', 'bot');
    document.getElementById('f').onsubmit = async (e) => {{
      e.preventDefault();
      const inp = document.getElementById('m');
      const text = inp.value.trim();
      if (!text) return;
      add(text, 'user');
      inp.value = '';
      try {{
        const r = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ message: text }})
        }});
        const data = await r.json();
        add(data.reply, 'bot');
      }} catch (err) {{
        add('出错了：' + err, 'bot');
      }}
    }};
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    cat_counts = {}
    for m in MOVIES:
        for c in (x.strip() for x in m["categories"].split(",") if x.strip()):
            cat_counts[c] = cat_counts.get(c, 0) + 1
    genres = sorted(cat_counts, key=lambda c: (-cat_counts[c], c))  # most common first
    chips = '<button class="chip active" data-cat="">全部</button>' + "".join(
        f'<button class="chip" data-cat="{c}">{c} ({cat_counts[c]})</button>' for c in genres
    )

    cards = []
    for m in MOVIES:
        search = f"{m['title']} {m['categories']} {m['regions']}".lower()
        pills = "".join(
            f'<span class="tag">{c.strip()}</span>'
            for c in m["categories"].split(",") if c.strip()
        )
        try:
            full = round(float(m["rating"] or 0))
        except ValueError:
            full = 0
        stars = "★" * full + "☆" * (5 - full)
        cards.append(f"""
        <article class="card" data-search="{search}" data-cats="{m['categories']}">
          <a class="poster" href="{m['detail_url']}" target="_blank">
            <img src="{m['poster']}" alt="{m['title']}" loading="lazy">
            <span class="badge">{m['score']}</span>
            <span class="overlay">查看详情 →</span>
          </a>
          <div class="info">
            <h3 title="{m['title']}">{m['title']}</h3>
            <div class="tags">{pills}</div>
            <p class="meta">{m['regions']} · {m['minutes']}</p>
            <div class="foot">
              <span class="date">{m['release_date']}</span>
              <span class="stars" title="{m['rating']}">{stars}</span>
            </div>
          </div>
        </article>""")
    return f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ssr1 Movies</title>
  <style>
    * {{ box-sizing: border-box; }}
    :root {{ --bg: #f4f6fb; --surface: #fff; --text: #1c2230; --muted: #6b7280;
             --line: #e6e9f0; --accent: #4f6ef7; --accent-2: #7c8cff; --gold: #f5a623; }}
    body {{ font-family: "Segoe UI", system-ui, sans-serif; margin: 0; color: var(--text);
            background: var(--bg); }}
    a {{ text-decoration: none; color: inherit; }}

    /* hero banner with the search bar */
    .hero {{ background: linear-gradient(135deg, #4f6ef7 0%, #7c8cff 55%, #9d7bff 100%);
             color: #fff; padding: 48px 24px 56px; text-align: center; }}
    .hero .logo {{ font-size: 40px; }}
    .hero h1 {{ margin: 8px 0 4px; font-size: 32px; font-weight: 800; letter-spacing: .5px; }}
    .hero p {{ margin: 0 0 26px; opacity: .9; font-size: 15px; }}
    .searchwrap {{ position: relative; max-width: 560px; margin: 0 auto; }}
    .searchwrap::before {{ content: "🔍"; position: absolute; left: 18px; top: 50%;
                           transform: translateY(-50%); font-size: 16px; opacity: .5; }}
    #search {{ width: 100%; padding: 15px 18px 15px 46px; border: 0; border-radius: 30px;
               font-size: 16px; outline: none; color: var(--text);
               box-shadow: 0 10px 30px rgba(0,0,0,.18); }}
    #count {{ display: inline-block; margin-top: 14px; font-size: 13px; color: #fff; opacity: .85; }}

    .chips {{ position: sticky; top: 0; z-index: 800; display: flex; flex-wrap: wrap;
              gap: 8px; justify-content: center; padding: 14px 24px;
              background: rgba(244,246,251,.9); backdrop-filter: blur(10px);
              border-bottom: 1px solid var(--line); }}
    .chip {{ border: 1px solid var(--line); background: var(--surface); color: var(--muted);
             padding: 6px 14px; border-radius: 18px; font-size: 13px; cursor: pointer;
             transition: all .15s; }}
    .chip:hover {{ color: var(--accent); border-color: var(--accent); }}
    .chip.active {{ background: var(--accent); border-color: var(--accent); color: #fff;
                    font-weight: 600; }}

    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
             gap: 24px; padding: 28px max(24px, 4vw); max-width: 1500px; margin: 0 auto; }}
    .card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
             overflow: hidden; display: flex; flex-direction: column;
             box-shadow: 0 1px 3px rgba(20,30,60,.06);
             transition: transform .2s, box-shadow .2s; }}
    .card:hover {{ transform: translateY(-6px); box-shadow: 0 16px 32px rgba(30,40,80,.16); }}
    .poster {{ position: relative; display: block; aspect-ratio: 2/3; overflow: hidden; }}
    .poster img {{ width: 100%; height: 100%; object-fit: cover; display: block;
                   transition: transform .35s; }}
    .card:hover .poster img {{ transform: scale(1.07); }}
    .badge {{ position: absolute; top: 10px; right: 10px; background: var(--gold); color: #fff;
              font-weight: 800; font-size: 13px; padding: 3px 9px; border-radius: 8px;
              box-shadow: 0 2px 8px rgba(0,0,0,.25); }}
    .overlay {{ position: absolute; left: 0; right: 0; bottom: 0; padding: 28px 12px 10px;
                font-size: 13px; font-weight: 600; color: #fff; opacity: 0;
                background: linear-gradient(transparent, rgba(0,0,0,.8)); transition: opacity .25s; }}
    .card:hover .overlay {{ opacity: 1; }}
    .info {{ padding: 13px 14px 15px; display: flex; flex-direction: column; gap: 8px; flex: 1; }}
    .info h3 {{ font-size: 14.5px; margin: 0; line-height: 1.3; font-weight: 700;
                display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                overflow: hidden; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 5px; }}
    .tag {{ font-size: 11px; color: var(--accent); background: rgba(79,110,247,.08);
            border: 1px solid rgba(79,110,247,.2); padding: 2px 8px; border-radius: 10px; }}
    .meta {{ margin: 0; font-size: 12px; color: var(--muted); }}
    .foot {{ margin-top: auto; display: flex; justify-content: space-between; align-items: center; }}
    .date {{ font-size: 12px; color: var(--muted); }}
    .stars {{ font-size: 12px; color: var(--gold); letter-spacing: 1px; }}
    #empty {{ display: none; text-align: center; color: var(--muted); padding: 60px; font-size: 16px; }}

    /* floating chatbot widget */
    #cbtn {{ position: fixed; right: 24px; bottom: 24px; width: 58px; height: 58px;
             border-radius: 50%; border: 0; font-size: 26px; cursor: pointer; z-index: 1000;
             background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fff;
             box-shadow: 0 6px 18px rgba(79,110,247,.45); transition: transform .15s; }}
    #cbtn:hover {{ transform: scale(1.08); }}
    #cwin {{ position: fixed; right: 24px; bottom: 94px; width: 350px; height: 470px;
             background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
             box-shadow: 0 12px 40px rgba(20,30,60,.25); display: none; flex-direction: column;
             overflow: hidden; z-index: 1000; }}
    #cwin.open {{ display: flex; }}
    #chead {{ background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fff;
              padding: 14px 16px; font-weight: 700; display: flex; justify-content: space-between; }}
    #cclose {{ cursor: pointer; opacity: .8; }}
    #cclose:hover {{ opacity: 1; }}
    #clog {{ flex: 1; overflow-y: auto; padding: 14px; background: #f7f8fc; }}
    #clog .m {{ max-width: 82%; padding: 9px 13px; border-radius: 14px; margin: 7px 0;
                white-space: pre-wrap; line-height: 1.45; font-size: 14px; }}
    #clog .u {{ background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fff;
                margin-left: auto; }}
    #clog .b {{ background: #fff; color: var(--text); border: 1px solid var(--line); }}
    #cform {{ display: flex; gap: 6px; padding: 10px; border-top: 1px solid var(--line); }}
    #cinput {{ flex: 1; padding: 9px 13px; border: 1px solid var(--line); border-radius: 10px;
               font-size: 14px; outline: none; }}
    #cinput:focus {{ border-color: var(--accent); }}
    #cform button {{ border: 0; background: linear-gradient(135deg, var(--accent), var(--accent-2));
                     color: #fff; border-radius: 10px; padding: 0 16px; cursor: pointer;
                     font-size: 16px; }}
    #csugg {{ display: flex; flex-wrap: wrap; gap: 6px; padding: 0 12px 8px; }}
    #csugg button {{ border: 1px solid rgba(79,110,247,.3); background: rgba(79,110,247,.08);
                     color: var(--accent); border-radius: 14px; padding: 5px 10px; font-size: 12.5px;
                     cursor: pointer; }}
    #csugg button:hover {{ background: var(--accent); color: #fff; }}
  </style>
</head>
<body>
  <section class="hero">
    <div class="logo">🎬</div>
    <h1>ssr1 Movies</h1>
    <p>{len(MOVIES)} 部经典电影 · 来自 ssr1.scrape.center</p>
    <div class="searchwrap">
      <input id="search" type="search" placeholder="搜索电影 / 类型 / 地区 …" autocomplete="off">
    </div>
    <div><span id="count"></span></div>
  </section>
  <div class="chips">{chips}</div>
  <div class="grid">{''.join(cards)}</div>
  <div id="empty">没有匹配的电影 🎬</div>
  <script>
    const cards = Array.from(document.querySelectorAll('.card'));
    const count = document.getElementById('count');
    const searchBox = document.getElementById('search');
    let activeCat = '';
    const update = () => {{
      const q = searchBox.value.trim().toLowerCase();
      let shown = 0;
      for (const c of cards) {{
        const matchText = !q || c.dataset.search.includes(q);
        const matchCat = !activeCat || c.dataset.cats.split(', ').includes(activeCat);
        const hit = matchText && matchCat;
        c.style.display = hit ? '' : 'none';
        if (hit) shown++;
      }}
      count.textContent = shown + ' / ' + cards.length;
      document.getElementById('empty').style.display = shown ? 'none' : 'block';
    }};
    searchBox.addEventListener('input', update);
    document.querySelectorAll('.chip').forEach(chip => {{
      chip.addEventListener('click', () => {{
        document.querySelector('.chip.active').classList.remove('active');
        chip.classList.add('active');
        activeCat = chip.dataset.cat;
        update();
      }});
    }});
    update();
  </script>

  <button id="cbtn" title="Ask the chatbot">💬</button>
  <div id="cwin">
    <div id="chead"><span>🎬 Movie Chatbot</span><span id="cclose">✕</span></div>
    <div id="clog"></div>
    <div id="csugg">
      <button>评分最高的电影</button>
      <button>推荐一部喜剧片</button>
      <button>1994年有哪些电影？</button>
    </div>
    <form id="cform">
      <input id="cinput" placeholder="问我关于电影的问题…" autocomplete="off">
      <button type="submit">↑</button>
    </form>
  </div>
  <script>
    const cbtn = document.getElementById('cbtn');
    const cwin = document.getElementById('cwin');
    const clog = document.getElementById('clog');
    const cinput = document.getElementById('cinput');
    let greeted = false;
    const cadd = (text, who) => {{
      const d = document.createElement('div');
      d.className = 'm ' + who;
      d.textContent = text;
      clog.appendChild(d);
      clog.scrollTop = clog.scrollHeight;
      return d;
    }};
    cbtn.onclick = () => {{
      cwin.classList.toggle('open');
      if (cwin.classList.contains('open')) {{
        if (!greeted) {{ cadd('你好！问我关于这些电影的任何问题，例如“评分最高的电影”。', 'b'); greeted = true; }}
        cinput.focus();
      }}
    }};
    document.getElementById('cclose').onclick = () => cwin.classList.remove('open');
    const send = async (text) => {{
      text = text.trim();
      if (!text) return;
      cadd(text, 'u');
      cinput.value = '';
      const wait = cadd('…', 'b');
      try {{
        const r = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ message: text }})
        }});
        const data = await r.json();
        wait.textContent = data.reply;
      }} catch (err) {{
        wait.textContent = '出错了：' + err;
      }}
      clog.scrollTop = clog.scrollHeight;
    }};
    document.querySelectorAll('#csugg button').forEach(b => {{
      b.onclick = () => send(b.textContent);
    }});
    document.getElementById('cform').onsubmit = (e) => {{
      e.preventDefault();
      send(cinput.value);
    }};
  </script>
</body>
</html>"""
