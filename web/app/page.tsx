"use client";

import { useMemo, useState } from "react";
import moviesData from "@/data/movies.json";
import type { Movie } from "@/lib/types";
import ChatWidget from "@/components/ChatWidget";

const movies = moviesData as Movie[];

function genresOf(m: Movie) {
  return m.categories.split(",").map((s) => s.trim()).filter(Boolean);
}

function stars(rating: string) {
  const full = Math.round(parseFloat(rating || "0"));
  return "★".repeat(full) + "☆".repeat(Math.max(0, 5 - full));
}

export default function Home() {
  const [q, setQ] = useState("");
  const [active, setActive] = useState<string[]>([]);

  const genres = useMemo(() => {
    const count = new Map<string, number>();
    for (const m of movies)
      for (const g of genresOf(m)) count.set(g, (count.get(g) || 0) + 1);
    return [...count.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, []);

  const shown = useMemo(
    () =>
      movies.filter((m) => {
        const text = `${m.title} ${m.categories} ${m.regions}`.toLowerCase();
        if (q && !text.includes(q.toLowerCase())) return false;
        if (active.length && !active.some((a) => genresOf(m).includes(a))) return false;
        return true;
      }),
    [q, active]
  );

  const toggle = (g: string) =>
    setActive((a) => (a.includes(g) ? a.filter((x) => x !== g) : [...a, g]));

  return (
    <main>
      {/* hero */}
      <section className="relative overflow-hidden border-b border-neutral-800">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(900px_400px_at_70%_-10%,rgba(99,102,241,0.35),transparent)]" />
        <div className="relative mx-auto max-w-6xl px-6 py-16 text-center">
          <div className="text-5xl">🎬</div>
          <h1 className="mt-3 bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent sm:text-5xl">
            ssr1 Movies
          </h1>
          <p className="mt-3 text-neutral-400">
            {movies.length} 部经典电影 · 来自 ssr1.scrape.center
          </p>
          <div className="relative mx-auto mt-8 max-w-xl">
            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500">
              🔍
            </span>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="搜索电影 / 类型 / 地区 …"
              className="w-full rounded-full border border-neutral-700 bg-neutral-900/80 py-3 pl-11 pr-4 text-[15px] text-neutral-100 outline-none transition placeholder:text-neutral-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>
        </div>
      </section>

      {/* category chips */}
      <div className="sticky top-0 z-30 border-b border-neutral-800 bg-neutral-950/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap justify-center gap-2 px-6 py-3">
          <button
            onClick={() => setActive([])}
            className={`rounded-full border px-3.5 py-1.5 text-[13px] transition ${
              active.length === 0
                ? "border-indigo-500 bg-indigo-500 font-semibold text-white"
                : "border-neutral-700 bg-neutral-900 text-neutral-400 hover:border-indigo-500 hover:text-white"
            }`}
          >
            全部
          </button>
          {genres.map(([g, n]) => (
            <button
              key={g}
              onClick={() => toggle(g)}
              className={`rounded-full border px-3.5 py-1.5 text-[13px] transition ${
                active.includes(g)
                  ? "border-indigo-500 bg-indigo-500 font-semibold text-white"
                  : "border-neutral-700 bg-neutral-900 text-neutral-400 hover:border-indigo-500 hover:text-white"
              }`}
            >
              {g} <span className="opacity-60">{n}</span>
            </button>
          ))}
        </div>
      </div>

      {/* grid */}
      <div className="mx-auto max-w-7xl px-6 pb-28 pt-6">
        <p className="mb-4 text-sm text-neutral-500">
          <span className="font-semibold text-neutral-300">{shown.length}</span> / {movies.length} 部电影
        </p>
        {shown.length === 0 ? (
          <p className="py-20 text-center text-neutral-500">没有匹配的电影 🎬</p>
        ) : (
          <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {shown.map((m) => (
              <a
                key={m.id}
                href={m.detail_url}
                target="_blank"
                rel="noreferrer"
                className="group overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-md transition duration-200 hover:-translate-y-1.5 hover:border-indigo-500/50 hover:shadow-2xl hover:shadow-indigo-500/10"
              >
                <div className="relative aspect-[2/3] overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`/posters/${m.id}.jpg`}
                    alt={m.title}
                    loading="lazy"
                    className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                  />
                  <span className="absolute right-2 top-2 rounded-md bg-gold px-2 py-0.5 text-xs font-extrabold text-black shadow">
                    {m.score}
                  </span>
                </div>
                <div className="p-3">
                  <h3 className="line-clamp-2 text-sm font-semibold leading-snug">{m.title}</h3>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {genresOf(m).slice(0, 3).map((g) => (
                      <span
                        key={g}
                        className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10.5px] text-indigo-300"
                      >
                        {g}
                      </span>
                    ))}
                  </div>
                  <p className="mt-1.5 text-xs text-neutral-500">
                    {m.regions} · {m.minutes}
                  </p>
                  <div className="mt-1 flex items-center justify-between text-xs">
                    <span className="text-neutral-500">{m.release_date}</span>
                    <span className="text-gold">{stars(m.rating)}</span>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>

      <ChatWidget />
    </main>
  );
}
