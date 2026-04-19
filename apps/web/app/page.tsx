import Link from "next/link";

import { RateCard } from "../components/rate-card";

const cards = [
  { currency: "港币", code: "HKD", rate: "100.00", hint: "基准金额" },
  { currency: "人民币", code: "CNY", rate: "87.08", hint: "刚刚更新" },
  { currency: "美元", code: "USD", rate: "12.79", hint: "实时参考" },
];

const trendPoints = [92, 88, 85, 81, 76, 71, 69, 64, 60, 63, 58, 57];

export default function Page() {
  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#32B56D_0%,#27A860_100%)] text-ink">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-8 px-6 py-8 lg:px-10 lg:py-12">
        <header className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="overflow-hidden rounded-panel bg-white shadow-soft">
            <div className="bg-[linear-gradient(135deg,#F8EFCF_0%,#F2D98B_100%)] px-8 py-7">
              <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-black/40">SmartFX 仪表盘</p>
                  <h1 className="mt-3 text-4xl font-semibold">今日汇率总览</h1>
                  <p className="mt-3 max-w-2xl text-base text-black/55">
                    用网页端方式集中查看实时汇率、AI 每日简报、AI 对话助手，以及专业版的结算分析能力。
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <div className="rounded-full bg-[#1C2A4B] px-4 py-2 text-sm font-medium text-white">AI 汇率助手</div>
                  <Link
                    href="/login"
                    className="rounded-full border border-black/10 bg-white/80 px-5 py-2 text-sm text-black/70 transition hover:bg-white"
                  >
                    立即体验
                  </Link>
                  <Link
                    href="/report"
                    className="rounded-full bg-jade-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-jade-500"
                  >
                    查看 AI 简报
                  </Link>
                </div>
              </div>
            </div>

            <div className="grid gap-5 px-8 py-8 md:grid-cols-2 xl:grid-cols-3">
              {cards.map((card) => (
                <RateCard key={card.code} {...card} />
              ))}
            </div>
          </section>

          <section className="rounded-panel bg-white/94 p-7 shadow-soft backdrop-blur">
            <p className="text-sm uppercase tracking-[0.3em] text-black/40">AI 摘要</p>
            <h2 className="mt-3 text-3xl font-semibold">今日换汇提醒</h2>
            <div className="mt-6 space-y-4">
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">区间信号</p>
                <p className="mt-2 text-2xl font-semibold">中低位</p>
              </div>
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">短期判断</p>
                <p className="mt-2 text-lg leading-8 text-black/70">
                  如果这周有刚需换汇，可以先看 AI 简报，再结合 AI 对话助手讨论一次性执行还是分批执行。
                </p>
              </div>
              <div className="rounded-3xl border border-[#E7C36A]/50 bg-[linear-gradient(135deg,rgba(248,239,207,0.6)_0%,rgba(242,217,139,0.55)_100%)] p-5 text-sm leading-7 text-black/70">
                以上内容仅供信息参考，不构成任何投资建议。
              </div>
            </div>
          </section>
        </header>

        <section className="grid gap-8 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="rounded-panel bg-white px-8 py-7 shadow-soft">
            <div className="flex flex-col gap-4 border-b border-black/6 pb-6 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">汇率趋势</p>
                <h2 className="mt-2 text-3xl font-semibold">港币兑人民币</h2>
              </div>
              <div className="flex gap-3 text-sm">
                <button className="rounded-full border border-black/10 px-5 py-2 text-black/45">7 天</button>
                <button className="rounded-full border border-black/10 px-5 py-2 text-black/45">30 天</button>
                <button className="rounded-full bg-jade-500 px-5 py-2 font-medium text-white">6 个月</button>
              </div>
            </div>

            <div className="mt-6">
              <div className="mb-6 flex items-end justify-between">
                <div>
                  <p className="text-lg text-black/45">HKD / CNY</p>
                  <p className="font-display mt-2 text-6xl font-semibold">0.8708</p>
                  <p className="mt-2 text-black/40">市场参考价 0.8744</p>
                </div>
                <div className="rounded-full bg-[#F7FAF7] px-4 py-2 text-sm text-black/50">更新于 04-19 06:00</div>
              </div>

              <div className="grid h-[340px] grid-cols-12 items-end gap-3 rounded-[24px] bg-[#FAFBF8] px-4 pb-5 pt-8">
                {trendPoints.map((point, index) => (
                  <div key={index} className="flex h-full items-end">
                    <div
                      className="w-full rounded-full bg-[linear-gradient(180deg,rgba(231,195,106,0.95)_0%,rgba(180,126,44,0.95)_100%)]"
                      style={{ height: `${point}%` }}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-8">
            <section className="rounded-panel bg-white p-7 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">核心入口</p>
              <h2 className="mt-2 text-3xl font-semibold">主要功能</h2>
              <div className="mt-6 space-y-4 text-black/68">
                <Link href="/report" className="block rounded-3xl bg-[#F7FAF7] p-5 transition hover:bg-[#EFF6EF]">
                  <p className="text-xl font-semibold">AI 每日简报</p>
                  <p className="mt-2 leading-7 text-black/60">阅读今天的汇率摘要、信号判断和风险提示。</p>
                </Link>
                <Link href="/assistant" className="block rounded-3xl bg-[#F7FAF7] p-5 transition hover:bg-[#EFF6EF]">
                  <p className="text-xl font-semibold">AI 对话助手</p>
                  <p className="mt-2 leading-7 text-black/60">直接提问换汇节奏、区间高低位、刚需方案和分批策略。</p>
                </Link>
                <Link href="/records" className="block rounded-3xl bg-[#F7FAF7] p-5 transition hover:bg-[#EFF6EF]">
                  <p className="text-xl font-semibold">换汇记录</p>
                  <p className="mt-2 leading-7 text-black/60">查看最近换汇记录和参考盈亏变化。</p>
                </Link>
              </div>
            </section>

            <section className="rounded-panel bg-white p-7 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">专业版能力</p>
              <h2 className="mt-2 text-3xl font-semibold">结算工具</h2>
              <div className="mt-6 space-y-4 text-black/68">
                <Link href="/pro/settlement" className="block rounded-3xl bg-[#F7FAF7] p-5 transition hover:bg-[#EFF6EF]">
                  <p className="text-xl font-semibold">结算计算器</p>
                  <p className="mt-2 leading-7 text-black/60">输入币种、金额、到款日期和优化目标，获得结算分析建议。</p>
                </Link>
                <Link href="/pro/report" className="block rounded-3xl bg-[#F7FAF7] p-5 transition hover:bg-[#EFF6EF]">
                  <p className="text-xl font-semibold">结算报告</p>
                  <p className="mt-2 leading-7 text-black/60">基于结算分析异步生成 AI 报告，并查看任务状态与结果内容。</p>
                </Link>
              </div>
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}
