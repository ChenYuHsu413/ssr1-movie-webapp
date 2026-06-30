"""Chatbot over the scraped movie catalog.

Backends, chosen automatically in this order:
  * Groq    - used when GROQ_API_KEY is set (model from GROQ_MODEL env).
  * Gemini  - used when GEMINI_API_KEY (or GOOGLE_API_KEY) is set.
  * Claude  - used when ANTHROPIC_API_KEY is set.
  * Local   - rule-based fallback over the structured data (works offline).
"""
import os
import re

CLAUDE_MODEL = "claude-sonnet-4-6"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM = (
    "You are a helpful assistant for a movie website. Answer questions ONLY "
    "using the movie catalog below. Be concise. Reply in the user's language.\n\n"
    "CATALOG:\n{catalog}"
)


def _catalog(movies):
    return "\n".join(
        f"{m['id']}. {m['title']} | 分类: {m['categories']} | 地区: {m['regions']} | "
        f"片长: {m['minutes']} | 上映: {m['release_date']} | 评分: {m['score']}"
        for m in movies
    )


def _groq_answer(message, movies):
    from groq import Groq

    client = Groq()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM.format(catalog=_catalog(movies))},
            {"role": "user", "content": message},
        ],
    )
    return resp.choices[0].message.content


def _gemini_answer(message, movies):
    from google import genai
    from google.genai import types

    client = genai.Client()  # reads GEMINI_API_KEY or GOOGLE_API_KEY
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM.format(catalog=_catalog(movies)),
            max_output_tokens=1024,
        ),
    )
    return resp.text


def _claude_answer(message, movies):
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM.format(catalog=_catalog(movies)),
        messages=[{"role": "user", "content": message}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _fmt(m):
    return f"{m['title']} (评分 {m['score']}, {m['release_date']}, {m['categories']})"


def _local_answer(message, movies):
    q = message.strip().lower()

    if not q or any(w in q for w in ("help", "帮助", "怎么用", "what can")):
        return ("我可以回答关于这 {0} 部电影的问题，例如：\n"
                "• 评分最高的电影\n• 搜索片名（如 “肖申克”）\n"
                "• 某类型（如 “爱情”、“喜剧”）\n• 某地区（如 “美国”、“中国香港”）\n"
                "• 某年份（如 “1994”）\n• 随机推荐一部").format(len(movies))

    if any(w in q for w in ("多少部", "几部", "how many", "count", "总共")):
        return f"目前共有 {len(movies)} 部电影。"

    if any(w in q for w in ("最高", "最好", "top", "best", "highest", "推荐评分")):
        top = sorted(movies, key=lambda m: float(m["score"] or 0), reverse=True)[:5]
        return "评分最高的电影：\n" + "\n".join(f"• {_fmt(m)}" for m in top)

    if any(w in q for w in ("随机", "random", "recommend", "推荐")):
        # deterministic "random" based on message length to avoid Date/random bans
        m = movies[len(message) % len(movies)]
        return "为你推荐：" + _fmt(m)

    # year search
    year = re.search(r"(19|20)\d{2}", message)
    if year:
        y = year.group(0)
        hits = [m for m in movies if m["release_date"].startswith(y)]
        if hits:
            return f"{y} 年上映的电影：\n" + "\n".join(f"• {_fmt(m)}" for m in hits)
        return f"没有找到 {y} 年上映的电影。"

    # free-text match against title / categories / regions
    hits = [m for m in movies
            if q in m["title"].lower()
            or q in m["categories"].lower()
            or q in m["regions"].lower()]
    if hits:
        head = f"找到 {len(hits)} 部相关电影：\n"
        return head + "\n".join(f"• {_fmt(m)}" for m in hits[:10])

    return ("抱歉，我没找到相关电影。试试片名关键词、类型（如 “剧情”）、"
            "地区（如 “美国”）、年份，或输入 “帮助”。")


def answer(message, movies):
    # Try each configured cloud provider in order; on failure cascade to the
    # next, and only fall back to the local search if all of them fail.
    providers = []
    if os.getenv("GROQ_API_KEY"):
        providers.append(("Groq", _groq_answer))
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        providers.append(("Gemini", _gemini_answer))
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("Claude", _claude_answer))

    failed = []
    for name, fn in providers:
        try:
            return fn(message, movies)
        except Exception:
            failed.append(name)

    note = f"({'/'.join(failed)} 调用失败，已回退到本地搜索)\n" if failed else ""
    return note + _local_answer(message, movies)
