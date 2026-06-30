"""Streamlit version of the ssr1 movie site (for Streamlit Community Cloud).

Reuses db.load_movies() for data and chatbot.answer() for the assistant.
Run locally:   streamlit run streamlit_app.py
"""
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


movies = get_movies()

st.title("🎬 ssr1 Movies")
st.caption(f"{len(movies)} 部经典电影 · 来自 ssr1.scrape.center")

# ---------- filters ----------
query = st.text_input("🔍 搜索", placeholder="片名 / 类型 / 地区 …")
all_cats = sorted({c.strip() for m in movies
                   for c in m["categories"].split(",") if c.strip()})
chosen = st.pills("类型筛选", all_cats, selection_mode="multi")


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
st.write(f"**{len(shown)} / {len(movies)}** 部电影")

# ---------- grid ----------
PER_ROW = 5
if not shown:
    st.info("没有匹配的电影 🎬")
for i in range(0, len(shown), PER_ROW):
    cols = st.columns(PER_ROW)
    for col, m in zip(cols, shown[i:i + PER_ROW]):
        with col:
            poster = os.path.join("posters", f"{m['id']}.jpg")
            if os.path.exists(poster):
                st.image(poster, width="stretch")
            st.markdown(f"**[{m['title']}]({m['detail_url']})**")
            st.caption(f"⭐ {m['score']}  ·  {m['release_date']}")
            st.caption(m["categories"])

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
