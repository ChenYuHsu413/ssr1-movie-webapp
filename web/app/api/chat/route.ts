import moviesData from "@/data/movies.json";
import type { Movie } from "@/lib/types";

const movies = moviesData as Movie[];
const MODEL = process.env.GEMINI_MODEL || "gemini-2.5-flash";

function catalog() {
  return movies
    .map(
      (m) =>
        `${m.id}. ${m.title} | 分类: ${m.categories} | 地区: ${m.regions} | 片长: ${m.minutes} | 上映: ${m.release_date} | 评分: ${m.score}`
    )
    .join("\n");
}

const SYSTEM =
  "You are a helpful assistant for a movie website. Answer questions ONLY using " +
  "the movie catalog below. Be concise. Reply in the user's language.\n\nCATALOG:\n" +
  catalog();

function fmt(m: Movie) {
  return `${m.title} (评分 ${m.score}, ${m.release_date}, ${m.categories})`;
}

function localAnswer(message: string): string {
  const q = (message || "").trim().toLowerCase();
  if (!q || ["help", "帮助", "怎么用"].some((w) => q.includes(w)))
    return `我可以回答关于这 ${movies.length} 部电影的问题，例如：评分最高的电影、某类型（爱情/喜剧）、某地区、某年份、随机推荐。`;
  if (["多少", "几部", "count", "总共"].some((w) => q.includes(w)))
    return `目前共有 ${movies.length} 部电影。`;
  if (["最高", "最好", "top", "best", "highest"].some((w) => q.includes(w))) {
    const top = [...movies]
      .sort((a, b) => parseFloat(b.score || "0") - parseFloat(a.score || "0"))
      .slice(0, 5);
    return "评分最高的电影：\n" + top.map((m) => "• " + fmt(m)).join("\n");
  }
  if (["随机", "random", "recommend", "推荐"].some((w) => q.includes(w))) {
    const m = movies[message.length % movies.length];
    return "为你推荐：" + fmt(m);
  }
  const ym = message.match(/(19|20)\d{2}/);
  if (ym) {
    const y = ym[0];
    const hits = movies.filter((m) => m.release_date.startsWith(y));
    return hits.length
      ? `${y} 年上映的电影：\n` + hits.map((m) => "• " + fmt(m)).join("\n")
      : `没有找到 ${y} 年上映的电影。`;
  }
  const hits = movies.filter(
    (m) =>
      m.title.toLowerCase().includes(q) ||
      m.categories.toLowerCase().includes(q) ||
      m.regions.toLowerCase().includes(q)
  );
  if (hits.length)
    return `找到 ${hits.length} 部相关电影：\n` + hits.slice(0, 10).map((m) => "• " + fmt(m)).join("\n");
  return "抱歉，我没找到相关电影。试试片名关键词、类型（如 剧情）、地区（如 美国）、年份，或输入 帮助。";
}

export async function POST(req: Request) {
  let message = "";
  try {
    ({ message } = await req.json());
  } catch {
    return Response.json({ reply: "请输入问题。" }, { status: 400 });
  }

  const key = process.env.GEMINI_API_KEY;
  if (!key) return Response.json({ reply: localAnswer(message) });

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${key}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: SYSTEM }] },
        contents: [{ role: "user", parts: [{ text: message }] }],
        generationConfig: { maxOutputTokens: 1024 },
      }),
    });
    if (!res.ok) throw new Error(`Gemini ${res.status}`);
    const data = await res.json();
    const reply =
      data?.candidates?.[0]?.content?.parts?.map((p: any) => p.text).join("") ||
      localAnswer(message);
    return Response.json({ reply });
  } catch (e: any) {
    return Response.json({
      reply: `(Gemini 调用失败：${e.message}，已回退到本地搜索)\n` + localAnswer(message),
    });
  }
}
