import Link from "next/link";

const sampleRecords = [
  { pair: "USD/CNY", amount: "10,000 USD", rate: "7.1800", pnl: "+120.00 CNY", date: "2026-04-19" },
  { pair: "HKD/CNY", amount: "20,000 HKD", rate: "0.9180", pnl: "-48.00 CNY", date: "2026-04-14" },
];

export default function RecordsPage() {
  return (
    <main className="min-h-screen bg-[#F5F7F4] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1320px] space-y-8">
        <header className="rounded-panel bg-[linear-gradient(135deg,#32B56D_0%,#27A860_100%)] p-8 text-white shadow-soft">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-white/70">换汇记录</p>
              <h1 className="mt-3 text-4xl font-semibold">我的记录</h1>
              <p className="mt-3 max-w-2xl text-base leading-8 text-white/80">
                这里展示最近的换汇记录、参考盈亏和基础概览，方便和 AI 简报、AI 对话联动查看。
              </p>
            </div>
            <div className="flex gap-3">
              <button className="rounded-full bg-white px-5 py-3 text-sm font-medium text-jade-600">新增记录</button>
              <Link href="/" className="rounded-full border border-white/25 px-5 py-3 text-sm text-white/85">
                返回首页
              </Link>
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="rounded-panel bg-white p-7 shadow-soft">
            <p className="text-sm uppercase tracking-[0.28em] text-black/40">概览</p>
            <h2 className="mt-2 text-3xl font-semibold">记录总览</h2>
            <div className="mt-6 space-y-4">
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">总记录数</p>
                <p className="mt-2 text-4xl font-semibold">2</p>
              </div>
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">参考盈亏</p>
                <p className="mt-2 text-4xl font-semibold text-jade-600">+72.00 CNY</p>
              </div>
            </div>
          </div>

          <div className="rounded-panel bg-white p-7 shadow-soft">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">记录列表</p>
                <h2 className="mt-2 text-3xl font-semibold">最近换汇明细</h2>
              </div>
              <button className="rounded-full border border-black/10 px-5 py-2 text-sm text-black/60">导出 CSV</button>
            </div>

            <div className="space-y-4">
              {sampleRecords.map((record) => (
                <article key={`${record.pair}-${record.date}`} className="rounded-3xl border border-black/6 bg-[#FBFCFA] p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="text-xl font-semibold">{record.pair}</p>
                      <p className="mt-1 text-black/55">{record.amount}</p>
                    </div>
                    <div className="grid gap-1 text-sm text-black/55 md:text-right">
                      <p>成交汇率 {record.rate}</p>
                      <p>参考盈亏 {record.pnl}</p>
                      <p>{record.date}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
