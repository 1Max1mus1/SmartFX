"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ensureDemoAuth } from "../../lib/demo-auth";

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enterDemo(target: "/report" | "/assistant" | "/pro/settlement") {
    setIsLoading(true);
    setError(null);

    try {
      await ensureDemoAuth();
      router.push(target);
    } catch (err) {
      setError(err instanceof Error ? err.message : "进入体验失败");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#32B56D_0%,#27A860_100%)] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto grid max-w-[1200px] gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-panel bg-white/95 p-8 shadow-soft">
          <p className="text-sm uppercase tracking-[0.3em] text-black/40">演示入口</p>
          <h1 className="mt-3 text-4xl font-semibold">进入 SmartFX</h1>
          <p className="mt-4 text-base leading-8 text-black/60">
            当前登录与注册采用演示模式，不需要真实校验邮箱和密码。进入后可以直接体验 AI 简报、AI 对话，以及专业版结算工具。
          </p>
          <div className="mt-8 rounded-3xl bg-[linear-gradient(135deg,#F8EFCF_0%,#F2D98B_100%)] p-6 text-sm leading-7 text-black/70">
            演示身份默认开放专业版能力，方便你完整查看结算计算器和结算报告。
          </div>
        </section>

        <section className="rounded-panel bg-white p-8 shadow-soft">
          <div className="grid gap-5">
            <div>
              <label className="mb-2 block text-sm text-black/45">演示邮箱</label>
              <div className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4">demo@smartfx.ai</div>
            </div>
            <div>
              <label className="mb-2 block text-sm text-black/45">演示密码</label>
              <div className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4">smartfxdemo</div>
            </div>
            <div className="rounded-3xl bg-[#F7FAF7] p-5 text-sm leading-7 text-black/60">
              所有入口都会自动创建或复用演示身份，不会因为数据库账号状态不同而阻塞你查看页面。
            </div>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <div className="flex flex-wrap gap-3 pt-2">
              <button
                className="rounded-full bg-jade-600 px-6 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isLoading}
                onClick={() => enterDemo("/report")}
              >
                {isLoading ? "进入中..." : "打开 AI 简报"}
              </button>
              <button
                className="rounded-full border border-black/10 px-6 py-3 text-black/70 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isLoading}
                onClick={() => enterDemo("/assistant")}
              >
                打开 AI 对话
              </button>
              <button
                className="rounded-full border border-black/10 px-6 py-3 text-black/70 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isLoading}
                onClick={() => enterDemo("/pro/settlement")}
              >
                打开专业版结算
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
