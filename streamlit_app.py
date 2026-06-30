"""Streamlit version of the ssr1 movie site (for Streamlit Community Cloud).

Reuses db.load_movies() for data and chatbot.answer() for the assistant.
Run locally:   streamlit run streamlit_app.py
"""
import base64
import html
import os

import streamlit as st

from db import load_movies
from chatbot import answer

# Expose any Streamlit secrets as env vars so chatbot.answer() (which reads
# os.getenv) can find the API keys. Safe no-op when no secrets are configured.
for _k in ("GROQ_API_KEY", "GROQ_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL",
           "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
    try:
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
    except Exception:
        pass

st.set_page_config(page_title="ssr1 Movies", page_icon="🎬", layout="wide")


@st.cache_data
def get_movies():
    return load_movies()


@st.cache_data
def poster_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


movies = get_movies()

# ---------- styling ----------
st.markdown("""
<style>
  #MainMenu, footer {visibility: hidden;}
  .block-container {padding-top: 1.2rem; max-width: 1500px;}
  .hero {background: linear-gradient(135deg,#4f6ef7 0%,#7c8cff 55%,#9d7bff 100%);
         color:#fff; border-radius:18px; padding:30px 28px; text-align:center;
         margin-bottom:18px;}
  .hero h1 {margin:0; font-size:30px; font-weight:800;}
  .hero p {margin:6px 0 0; opacity:.9;}
  .grid {display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr));
         gap:20px; margin-top:8px;}
  .card {background:#fff; border:1px solid #e6e9f0; border-radius:14px;
         overflow:hidden; box-shadow:0 1px 3px rgba(20,30,60,.06);
         transition:transform .2s, box-shadow .2s;}
  .card:hover {transform:translateY(-6px); box-shadow:0 16px 32px rgba(30,40,80,.16);}
  .poster {position:relative; aspect-ratio:2/3; background-size:cover;
           background-position:center;}
  .badge {position:absolute; top:8px; right:8px; background:#f5a623; color:#fff;
          font-weight:800; font-size:12px; padding:3px 8px; border-radius:8px;}
  .info {padding:11px 12px 13px;}
  .title {font-weight:700; font-size:14px; line-height:1.3; margin-bottom:6px;
          display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
          overflow:hidden;}
  .title a {color:#1c2230; text-decoration:none;}
  .tags {display:flex; flex-wrap:wrap; gap:4px; margin-bottom:6px;}
  .tag {font-size:10.5px; color:#4f6ef7; background:rgba(79,110,247,.08);
        border:1px solid rgba(79,110,247,.2); padding:1px 7px; border-radius:9px;}
  .meta {font-size:11.5px; color:#6b7280;}
  .foot {display:flex; justify-content:space-between; margin-top:4px; font-size:11.5px;}
  .stars {color:#f5a623; letter-spacing:1px;}
  .date {color:#6b7280;}
</style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div class="hero"><h1>🎬 ssr1 Movies</h1>'
    f'<p>{len(movies)} 部经典电影 · 来自 ssr1.scrape.center</p></div>',
    unsafe_allow_html=True,
)

# ---------- filters ----------
c1, c2 = st.columns([2, 3])
query = c1.text_input("🔍 搜索", placeholder="片名 / 类型 / 地区 …",
                      label_visibility="collapsed")
all_cats = sorted({c.strip() for m in movies
                   for c in m["categories"].split(",") if c.strip()})
with c2:
    chosen = st.pills("类型", all_cats, selection_mode="multi",
                      label_visibility="collapsed")


def keep(m):
    if query and query.lower() not in (
            f"{m['title']} {m['categories']} {m['regions']}".lower()):
        return False
    if chosen:
        cats = {c.strip() for c in m["categories"].split(",")}
        if not (set(chosen) & cats):  # show movies in ANY selected genre
            return False
    return True


shown = [m for m in movies if keep(m)]
st.caption(f"**{len(shown)} / {len(movies)}** 部电影")

# ---------- grid (custom HTML cards) ----------
if not shown:
    st.info("没有匹配的电影 🎬")
else:
    cards = []
    for m in shown:
        path = os.path.join("posters", f"{m['id']}.jpg")
        bg = (f"background-image:url(data:image/jpeg;base64,{poster_b64(path)})"
              if os.path.exists(path) else "background:#e6e9f0")
        try:
            full = round(float(m["rating"] or 0))
        except ValueError:
            full = 0
        stars = "★" * full + "☆" * (5 - full)
        tags = "".join(f'<span class="tag">{html.escape(c.strip())}</span>'
                       for c in m["categories"].split(",") if c.strip())
        cards.append(
            f'<div class="card">'
            f'<a href="{m["detail_url"]}" target="_blank">'
            f'<div class="poster" style="{bg}"><span class="badge">{m["score"]}</span></div></a>'
            f'<div class="info">'
            f'<div class="title"><a href="{m["detail_url"]}" target="_blank">{html.escape(m["title"])}</a></div>'
            f'<div class="tags">{tags}</div>'
            f'<div class="meta">{html.escape(m["regions"])} · {html.escape(m["minutes"])}</div>'
            f'<div class="foot"><span class="date">{m["release_date"]}</span>'
            f'<span class="stars">{stars}</span></div>'
            f'</div></div>'
        )
    st.markdown(f'<div class="grid">{"".join(cards)}</div>', unsafe_allow_html=True)

# ---------- chatbot (sidebar) ----------
with st.sidebar:
    st.header("💬 电影助手")
    if "msgs" not in st.session_state:
        st.session_state.msgs = [
            ("assistant", "你好！问我关于这些电影的问题，例如“评分最高的电影”。")]

    prompt = st.chat_input("问我关于电影的问题…")
    if prompt:
        st.session_state.msgs.append(("user", prompt))
        with st.spinner("思考中…"):
            st.session_state.msgs.append(("assistant", answer(prompt, movies)))

    for role, text in st.session_state.msgs:
        st.chat_message(role).write(text)
