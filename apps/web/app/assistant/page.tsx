"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { ensureDemoAuth } from "../../lib/demo-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";

type ChatMessage = {
  role: string;
  content: string;
  created_at: string;
};

type ChatPayload = {
  session_id: string;
  answer: string;
  messages: ChatMessage[];
};

const roleLabelMap: Record<string, string> = {
  user: "你",
  assistant: "AI 助手",
};

export default function AssistantPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("我这周要换 10000 美元，现在更适合一次性换还是分批换？");
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function boot() {
      try {
        await ensureDemoAuth();
        if (isMounted) {
          setIsReady(true);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "AI 对话初始化失败");
        }
      }
    }

    void boot();

    return () => {
      isMounted = false;
    };
  }, []);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.trim()) {
      return;
    }

    setIsSending(true);
    setError(null);

    try {
      const { token } = await ensureDemoAuth();
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: draft.trim(),
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`AI 对话请求失败：${response.status}`);
      }

      const payload = (await response.json()) as ChatPayload;
      setSessionId(payload.session_id);
      setMessages(payload.messages);
      setDraft("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI 对话请求失败");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#32B56D_0%,#27A860_100%)] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto grid max-w-[1360px] gap-8 lg:grid-cols-[0.7fr_1.3fr]">
        <section className="rounded-panel bg-white/95 p-8 shadow-soft">
          <p className="text-sm uppercase tracking-[0.3em] text-black/40">AI 对话助手</p>
          <h1 className="mt-3 text-4xl font-semibold">即时问答</h1>
          <p className="mt-4 text-base leading-8 text-black/60">
            这里已经接到后端对话接口。你可以直接问换汇节奏、区间高低位、刚需执行方案，或者你自己的具体金额场景。
          </p>

          <div className="mt-8 space-y-4">
            <div className="rounded-3xl bg-[#F7FAF7] p-5">
              <p className="text-sm text-black/40">可问范围</p>
              <p className="mt-2 leading-8 text-black/70">分批换汇、一次性执行、近期区间判断、结算窗口、记录参考和风险提示。</p>
            </div>
            <div className="rounded-3xl bg-[#F7FAF7] p-5">
              <p className="text-sm text-black/40">当前状态</p>
              <p className="mt-2 leading-8 text-black/70">{isReady ? "演示身份已就绪，可以直接开始提问。" : "正在准备演示身份..."}</p>
            </div>
            <div className="flex gap-3 pt-2">
              <Link href="/" className="rounded-full border border-black/10 px-5 py-3 text-sm text-black/70">
                返回首页
              </Link>
              <Link href="/report" className="rounded-full bg-white px-5 py-3 text-sm font-medium text-jade-600">
                打开 AI 简报
              </Link>
            </div>
          </div>
        </section>

        <section className="rounded-panel bg-white p-8 shadow-soft">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">会话内容</p>
              <h2 className="mt-2 text-3xl font-semibold">问答窗口</h2>
            </div>
            <span className="rounded-full bg-[#F7FAF7] px-4 py-2 text-sm text-black/50">
              {sessionId ? `会话 ${sessionId.slice(0, 8)}` : "等待第一条问题"}
            </span>
          </div>

          <div className="space-y-4">
            {messages.length === 0 ? (
              <article className="max-w-[78%] rounded-[28px] bg-[#F7FAF7] px-5 py-4 text-black/70">
                <p className="text-sm uppercase tracking-[0.2em] opacity-60">AI 助手</p>
                <p className="mt-2 leading-8">可以直接问我：现在换 1 万美元更适合分批还是一次性？</p>
              </article>
            ) : (
              messages.map((message, index) => (
                <article
                  key={`${message.role}-${index}-${message.created_at}`}
                  className={
                    message.role === "user"
                      ? "ml-auto max-w-[72%] rounded-[28px] bg-jade-600 px-5 py-4 text-white"
                      : "max-w-[78%] rounded-[28px] bg-[#F7FAF7] px-5 py-4 text-black/70"
                  }
                >
                  <p className="text-sm uppercase tracking-[0.2em] opacity-60">{roleLabelMap[message.role] ?? message.role}</p>
                  <p className="mt-2 whitespace-pre-wrap leading-8">{message.content}</p>
                </article>
              ))
            )}
          </div>

          <form className="mt-6 rounded-[28px] border border-black/8 bg-[#FBFCFA] p-4" onSubmit={submitQuestion}>
            <textarea
              className="min-h-[140px] w-full resize-none bg-transparent text-base outline-none"
              placeholder="请输入你的问题，例如：我准备在一周内换 10000 美元，应该如何安排更稳妥？"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
            <div className="mt-4 flex items-center justify-between gap-4">
              {error ? <p className="text-sm text-red-600">{error}</p> : <div />}
              <button
                className="rounded-full bg-jade-600 px-6 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!isReady || isSending}
                type="submit"
              >
                {isSending ? "发送中..." : "发送问题"}
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
