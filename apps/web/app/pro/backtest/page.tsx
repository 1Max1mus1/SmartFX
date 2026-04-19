import Link from "next/link";

const overviewRows = [
  { signal: "买入参考", total: 32, match7: "68%", match14: "64%" },
  { signal: "继续观察", total: 30, match7: "55%", match14: "58%" },
  { signal: "卖出参考", total: 28, match7: "71%", match14: "69%" },
];

export default function ProBacktestPage() {
  return (
    <main className="min-h-screen bg-[#F5F7F4] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1400px] space-y-8">
        <header className="rounded-panel bg-[linear-gradient(135deg,#F8EFCF_0%,#F2D98B_100%)] p-8 shadow-soft">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-black/40">专业版回测</p>
              <h1 className="mt-3 text-4xl font-semibold">回测系统</h1>
              <p className="mt-3 max-w-3xl text-base leading-8 text-black/60">
                这里用于查看历史信号的参考表现，以及个人换汇在历史区间里的模拟结果，帮助你理解策略节奏。
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/pro/settlement" className="rounded-full border border-black/10 px-5 py-3 text-sm text-black/70">
                返回专业版
              </Link>
              <Link href="/" className="rounded-full bg-jade-600 px-5 py-3 text-sm font-medium text-white">
                返回首页
              </Link>
            </div>
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
          <section className="rounded-panel bg-white p-8 shadow-soft">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">概览</p>
                <h2 className="mt-2 text-3xl font-semibold">信号吻合率看板</h2>
              </div>
              <div className="flex gap-3 text-sm">
                <button className="rounded-full border border-black/10 px-5 py-2 text-black/45">30 天</button>
                <button className="rounded-full border border-black/10 px-5 py-2 text-black/45">60 天</button>
                <button className="rounded-full bg-jade-500 px-5 py-2 font-medium text-white">90 天</button>
              </div>
            </div>

            <div className="mt-6 rounded-3xl bg-[#F7FAF7] p-5">
              <p className="text-sm text-black/40">综合参考指数</p>
              <p className="mt-2 text-5xl font-semibold">67.4</p>
              <p className="mt-2 text-black/55">仅作历史统计参考，不代表未来表现。</p>
            </div>

            <div className="mt-6 overflow-hidden rounded-3xl border border-black/6">
              <table className="w-full text-left">
                <thead className="bg-[#FBFCFA] text-sm text-black/45">
                  <tr>
                    <th className="px-5 py-4">信号</th>
                    <th className="px-5 py-4">次数</th>
                    <th className="px-5 py-4">7 日吻合率</th>
                    <th className="px-5 py-4">14 日吻合率</th>
                  </tr>
                </thead>
                <tbody>
                  {overviewRows.map((row) => (
                    <tr key={row.signal} className="border-t border-black/6">
                      <td className="px-5 py-4 font-medium">{row.signal}</td>
                      <td className="px-5 py-4">{row.total}</td>
                      <td className="px-5 py-4">{row.match7}</td>
                      <td className="px-5 py-4">{row.match14}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-panel bg-white p-8 shadow-soft">
            <p className="text-sm uppercase tracking-[0.28em] text-black/40">个人回测</p>
            <h2 className="mt-2 text-3xl font-semibold">个人换汇模拟</h2>
            <div className="mt-6 grid gap-5">
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm text-black/45">开始日期</label>
                  <input className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none" placeholder="2026-01-01" />
                </div>
                <div>
                  <label className="mb-2 block text-sm text-black/45">结束日期</label>
                  <input className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none" placeholder="2026-04-19" />
                </div>
              </div>
              <div>
                <label className="mb-2 block text-sm text-black/45">货币对</label>
                <div className="rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4">USD/CNY</div>
              </div>
              <button className="rounded-full bg-[#1C2A4B] px-6 py-4 font-medium text-white">开始回测</button>
            </div>

            <div className="mt-8 rounded-3xl border border-[#E7C36A]/40 bg-[linear-gradient(135deg,rgba(248,239,207,0.58)_0%,rgba(242,217,139,0.52)_100%)] p-6 text-base leading-8 text-black/70">
              历史模拟结果会展示实际平均换汇汇率、模拟平均汇率以及参考差额，仅供分析参考。
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
