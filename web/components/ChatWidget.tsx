"use client";

import { useEffect, useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; content: string };

const SUGGESTIONS: [string, string][] = [
  ["🏆 评分最高", "评分最高的电影"],
  ["😄 喜剧片", "喜剧"],
  ["📅 1994 年", "1994"],
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "assistant", content: "你好！问我关于这 100 部电影的任何问题，例如「评分最高的电影」。" },
  ]);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, loading, open]);

  async function send(text: string) {
    text = text.trim();
    if (!text || loading) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMsgs((m) => [...m, { role: "assistant", content: data.reply ?? "（没有回应）" }]);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "assistant", content: "出错了：" + e.message }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* toggle button */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="chat"
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-2xl shadow-lg shadow-indigo-500/40 transition hover:scale-110"
      >
        {open ? "✕" : "💬"}
      </button>

      {/* panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 flex h-[480px] w-[360px] max-w-[calc(100vw-3rem)] flex-col overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900 shadow-2xl">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3">
            <div className="font-bold">🎬 电影小助手</div>
            <div className="text-xs text-indigo-100/80">问我这 100 部电影的任何问题</div>
          </div>

          <div ref={logRef} className="flex-1 space-y-3 overflow-y-auto p-3">
            {msgs.map((m, i) => (
              <div key={i} className={`flex items-end gap-2 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                <div
                  className={`flex h-7 w-7 flex-none items-center justify-center rounded-full text-sm ${
                    m.role === "user" ? "bg-gradient-to-br from-indigo-500 to-purple-500" : "bg-neutral-800"
                  }`}
                >
                  {m.role === "user" ? "🙂" : "🎬"}
                </div>
                <div
                  className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-[13.5px] leading-relaxed ${
                    m.role === "user"
                      ? "rounded-br-sm bg-gradient-to-br from-indigo-500 to-purple-500 text-white"
                      : "rounded-bl-sm bg-neutral-800 text-neutral-100"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-end gap-2">
                <div className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-neutral-800 text-sm">🎬</div>
                <div className="rounded-2xl rounded-bl-sm bg-neutral-800 px-3 py-2 text-[13.5px] text-neutral-400">
                  思考中…
                </div>
              </div>
            )}
          </div>

          {/* suggestions */}
          <div className="flex flex-wrap gap-2 px-3 pb-2">
            {SUGGESTIONS.map(([label, q]) => (
              <button
                key={label}
                onClick={() => send(q)}
                disabled={loading}
                className="rounded-full border border-indigo-500/40 bg-indigo-500/10 px-2.5 py-1 text-xs text-indigo-300 transition hover:bg-indigo-500 hover:text-white disabled:opacity-50"
              >
                {label}
              </button>
            ))}
          </div>

          {/* input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="flex gap-2 border-t border-neutral-800 p-3"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入消息…"
              className="flex-1 rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 px-4 text-white transition hover:opacity-90 disabled:opacity-50"
            >
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  );
}
