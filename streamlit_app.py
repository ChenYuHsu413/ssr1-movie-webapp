"""Streamlit version of the ssr1 movie site (for Streamlit Community Cloud).

Reuses db.load_movies() for data and chatbot.answer() for the assistant.
Run locally:   streamlit run streamlit_app.py
"""
import base64
import html
import os

import streamlit as st
from streamlit_float import float_init, float_css_helper

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
float_init()  # enables floating containers (the chat widget)


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

  /* ----- chatbot ----- */
  /* round floating action button (closed state) */
  .st-key-chat_open_btn button {
    width:60px!important; height:60px!important; min-height:60px!important;
    border-radius:50%!important; padding:0!important;
    background:linear-gradient(135deg,#4f6ef7,#7c8cff)!important; color:#fff!important;
    border:none!important; box-shadow:0 6px 18px rgba(79,110,247,.45)!important;
    display:flex!important; align-items:center!important; justify-content:center!important;
    transition:transform .15s;}
  .st-key-chat_open_btn button:hover {transform:scale(1.08);}
  .st-key-chat_open_btn button p,
  .st-key-chat_open_btn button div {font-size:26px!important; margin:0!important;
    line-height:1!important;}
  /* close (✕) button */
  .st-key-chat_close button {
    background:transparent!important; border:none!important; color:#6b7280!important;
    box-shadow:none!important; font-size:18px!important;}
  .st-key-chat_close button:hover {color:#1c2230!important;}
  /* suggestion chips */
  [class*="st-key-sugg_"] button {
    border:1px solid rgba(79,110,247,.35)!important; background:rgba(79,110,247,.08)!important;
    color:#4f6ef7!important; border-radius:14px!important; font-size:12px!important;
    padding:4px 6px!important; min-height:0!important; font-weight:600;}
  [class*="st-key-sugg_"] button:hover {background:#4f6ef7!important; color:#fff!important;}
  /* send button */
  [data-testid="stFormSubmitButton"] button {
    background:linear-gradient(135deg,#4f6ef7,#7c8cff)!important; color:#fff!important;
    border:none!important; border-radius:10px!important;}
  /* gradient header bar (bleeds to panel edges) */
  .cbhead {margin:-14px -14px 12px; padding:13px 16px; color:#fff;
           background:linear-gradient(135deg,#4f6ef7,#7c8cff);
           border-radius:16px 16px 0 0;}
  .cbhead .t {font-weight:800; font-size:15px;}
  .cbhead .s {font-size:11.5px; opacity:.9; margin-top:1px;}
  /* close button, absolutely placed over the header */
  .st-key-chat_close {position:absolute!important; top:8px; right:10px; z-index:10;
                      width:auto!important;}
  .st-key-chat_close button {color:#fff!important; font-size:16px!important;}
  /* custom chat bubbles + auto-scroll to newest (column-reverse) */
  .chatlog {display:flex; flex-direction:column-reverse; gap:10px;
            overflow-y:auto; max-height:250px; padding:2px 2px 4px;}
  .row {display:flex; gap:8px; align-items:flex-end;}
  .row.user {flex-direction:row-reverse;}
  .av {width:28px; height:28px; border-radius:50%; flex:0 0 auto; font-size:15px;
       display:flex; align-items:center; justify-content:center;}
  .bav {background:#eef1ff;}
  .uav {background:linear-gradient(135deg,#4f6ef7,#7c8cff);}
  .bubble {max-width:75%; padding:8px 12px; border-radius:14px; font-size:13.5px;
           line-height:1.45; word-break:break-word;}
  .bbot {background:#f1f3f7; color:#1c2230; border-bottom-left-radius:4px;}
  .buser {background:linear-gradient(135deg,#4f6ef7,#7c8cff); color:#fff;
          border-bottom-right-radius:4px;}
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

# ---------- floating chatbot (bottom-right, in-page) ----------
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "msgs" not in st.session_state:
    st.session_state.msgs = [
        ("assistant", "你好！问我关于这些电影的问题，例如“评分最高的电影”。")]

# (label shown on the chip, query sent to the chatbot)
SUGGESTIONS = [("🏆 评分最高", "评分最高的电影"),
               ("😄 喜剧片", "喜剧"),
               ("📅 1994 年", "1994")]

widget = st.container()
with widget:
    if st.session_state.chat_open:
        if st.button("✕", key="chat_close"):
            st.session_state.chat_open = False
            st.rerun()
        st.markdown('<div class="cbhead"><div class="t">🎬 电影小助手</div>'
                    '<div class="s">问我这 100 部电影的任何问题</div></div>',
                    unsafe_allow_html=True)

        # message bubbles (reversed + column-reverse CSS = auto-scroll to newest)
        rows = ""
        for role, text in reversed(st.session_state.msgs):
            safe = html.escape(text).replace("\n", "<br>")
            if role == "user":
                rows += (f'<div class="row user"><div class="av uav">🙂</div>'
                         f'<div class="bubble buser">{safe}</div></div>')
            else:
                rows += (f'<div class="row"><div class="av bav">🎬</div>'
                         f'<div class="bubble bbot">{safe}</div></div>')
        st.markdown(f'<div class="chatlog">{rows}</div>', unsafe_allow_html=True)

        # quick-question shortcuts
        picked = None
        for i, (col, (label, q)) in enumerate(zip(st.columns(len(SUGGESTIONS)),
                                                   SUGGESTIONS)):
            if col.button(label, key=f"sugg_{i}", use_container_width=True):
                picked = q

        with st.form("chat_form", clear_on_submit=True, border=False):
            fi, fb = st.columns([5, 1])
            prompt = fi.text_input("msg", label_visibility="collapsed",
                                   placeholder="输入消息…")
            sent = fb.form_submit_button("➤")

        user_msg = picked or (prompt if sent and prompt else None)
        if user_msg:
            st.session_state.msgs.append(("user", user_msg))
            with st.spinner("思考中…"):
                st.session_state.msgs.append(("assistant", answer(user_msg, movies)))
            st.rerun()
        # opaque panel, anchored bottom-right
        css = float_css_helper(width="360px", right="2rem", bottom="2rem", shadow=12,
                               background="#ffffff", border="1px solid #e6e9f0",
                               css="border-radius:16px; padding:14px;")
    else:
        if st.button("💬", key="chat_open_btn"):
            st.session_state.chat_open = True
            st.rerun()
        # fixed width so streamlit-float doesn't stretch the button full-width
        css = float_css_helper(width="64px", right="2rem", bottom="2rem")
widget.float(css)
