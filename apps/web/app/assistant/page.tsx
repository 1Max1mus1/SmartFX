"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { MarkdownContent } from "../../components/markdown-content";
import { StudentPaymentAdvisorCard } from "../../components/student-payment-advisor-card";
import { authorizedDemoFetch, ensureDemoAuth } from "../../lib/demo-auth";

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
  user: "用户",
  assistant: "AI 助手",
};

export default function AssistantPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("我这周要换 10000 美元，现在更适合一次性处理还是分批安排？");
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
      } catch (bootError) {
        if (isMounted) {
          setError(bootError instanceof Error ? bootError.message : "AI 对话初始化失败");
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
      const response = await authorizedDemoFetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AI 对话请求失败");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#32B56D_0%,#27A860_100%)] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1380px] space-y-8">
        <header className="rounded-panel bg-white/95 p-8 shadow-soft">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-black/40">AI Assistant</p>
              <h1 className="mt-3 text-4xl font-semibold">即时问答与场景建议</h1>
              <p className="mt-4 max-w-4xl text-base leading-8 text-black/60">
                这个页面现在把常规的汇率对话助手和“留学生缴费助手”结合到了一起。你可以直接自由提问，也可以先拿到基于截止日的结构化建议，再继续往下追问细节。
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/" className="rounded-full border border-black/10 px-5 py-3 text-sm text-black/70">
                返回首页
              </Link>
              <Link href="/report" className="rounded-full bg-white px-5 py-3 text-sm font-medium text-jade-600">
                打开 AI 简报
              </Link>
            </div>
          </div>
        </header>

        <div className="grid gap-8 xl:grid-cols-[0.92fr_1.08fr]">
          <div className="space-y-8">
            <section className="rounded-panel bg-white/95 p-8 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">Capabilities</p>
              <h2 className="mt-2 text-3xl font-semibold">你现在可以这样用我</h2>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-3xl bg-[#F7FAF7] p-5">
                  <p className="text-sm text-black/40">自由问答</p>
                  <p className="mt-2 leading-8 text-black/70">
                    继续像以前一样，直接问换汇节奏、最近区间位置、短期观察窗口，或者是否适合分批执行。
                  </p>
                </div>
                <div className="rounded-3xl bg-[#F7FAF7] p-5">
                  <p className="text-sm text-black/40">留学生缴费场景</p>
                  <p className="mt-2 leading-8 text-black/70">
                    如果你的真实问题是“某个截止日之前该不该交学费”，建议先用下面的结构化助手，再继续往下追问更细的执行问题。
                  </p>
                </div>
                <div className="rounded-3xl bg-[#F7FAF7] p-5">
                  <p className="text-sm text-black/40">快捷问题</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {[
                      "今天适合缴学费吗？",
                      "当前汇率算不算低？",
                      "如果我只能操作一次，应该怎么安排？",
                    ].map((item) => (
                      <button
                        key={item}
                        className="rounded-full border border-black/10 px-4 py-2 text-sm text-black/70 transition hover:border-jade-600 hover:text-jade-700"
                        type="button"
                        onClick={() => setDraft(item)}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="rounded-3xl bg-[#F7FAF7] p-5">
                  <p className="text-sm text-black/40">当前状态</p>
                  <p className="mt-2 leading-8 text-black/70">
                    {isReady ? "演示身份已就绪，可以同时使用结构化建议和聊天窗口。" : "正在准备演示身份..."}
                  </p>
                </div>
              </div>
            </section>

            <StudentPaymentAdvisorCard
              isReady={isReady}
              onUseFollowUp={(message) => {
                setDraft(message);
              }}
            />
          </div>

          <section className="rounded-panel bg-white p-8 shadow-soft">
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">Conversation</p>
                <h2 className="mt-2 text-3xl font-semibold">问答窗口</h2>
              </div>
              <span className="rounded-full bg-[#F7FAF7] px-4 py-2 text-sm text-black/50">
                {sessionId ? `会话 ${sessionId.slice(0, 8)}` : "等待第一条问题"}
              </span>
            </div>

            <div className="space-y-4">
              {messages.length === 0 ? (
                <article className="max-w-[82%] rounded-[28px] bg-[#F7FAF7] px-5 py-4 text-black/70">
                  <p className="text-sm uppercase tracking-[0.2em] opacity-60">AI 助手</p>
                  <p className="mt-2 leading-8">
                    你可以直接问我：“我这周前要交学费，现在一次性换汇还是分批会更稳妥？”
                  </p>
                </article>
              ) : (
                messages.map((message, index) => (
                  <article
                    key={`${message.role}-${index}-${message.created_at}`}
                    className={
                      message.role === "user"
                        ? "ml-auto max-w-[76%] rounded-[28px] bg-jade-600 px-5 py-4 text-white"
                        : "max-w-[82%] rounded-[28px] bg-[#F7FAF7] px-5 py-4 text-black/70"
                    }
                  >
                    <p className="text-sm uppercase tracking-[0.2em] opacity-60">{roleLabelMap[message.role] ?? message.role}</p>
                    <div className="mt-2">
                      {message.role === "assistant" ? (
                        <MarkdownContent content={message.content} />
                      ) : (
                        <p className="whitespace-pre-wrap leading-8">{message.content}</p>
                      )}
                    </div>
                  </article>
                ))
              )}
            </div>

            <form className="mt-6 rounded-[28px] border border-black/8 bg-[#FBFCFA] p-4" onSubmit={submitQuestion}>
              <textarea
                className="min-h-[160px] w-full resize-none bg-transparent text-base outline-none"
                placeholder="请输入你的问题，比如汇率时机、缴费安排，或者继续追问上面的建议为什么这么给。"
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
      </div>
    </main>
  );
}
