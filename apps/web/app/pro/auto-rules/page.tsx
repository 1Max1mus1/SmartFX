import Link from "next/link";

const rules = [
  {
    title: "汇率触发",
    pair: "USD/CNY",
    condition: "高于 7.2000",
    cooldown: "120 分钟",
    status: "已启用",
  },
  {
    title: "AI 信号触发",
    pair: "HKD/CNY",
    condition: "信号 = 买入参考",
    cooldown: "240 分钟",
    status: "静默时段 01:00-07:00",
  },
];

const historyItems = [
  {
    time: "2026-04-19 08:30",
    title: "USD/CNY 到达目标价位",
    detail: "系统只发送提醒通知，没有执行真实换汇操作。",
  },
  {
    time: "2026-04-18 08:30",
    title: "AI 每日信号命中买入规则",
    detail: "系统建议先复核结算窗口，再决定是否手动执行。",
  },
];

export default function AutoRulesPage() {
  return (
    <main className="min-h-screen bg-[#F5F7F4] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1400px] space-y-8">
        <header className="rounded-panel bg-[linear-gradient(135deg,#F8EFCF_0%,#F2D98B_100%)] p-8 shadow-soft">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-black/40">自动化规则</p>
              <h1 className="mt-3 text-4xl font-semibold">半自动决策中心</h1>
              <p className="mt-3 max-w-3xl text-base leading-8 text-black/60">
                这里保留 SmartFX 的绿色金色视觉风格，但只承担提醒和参考作用，不会自动执行真实换汇。
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/pro/backtest" className="rounded-full border border-black/10 px-5 py-3 text-sm text-black/70">
                回测系统
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
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">规则列表</p>
                <h2 className="mt-2 text-3xl font-semibold">规则中心</h2>
              </div>
              <button className="rounded-full bg-[#1C2A4B] px-5 py-3 text-sm font-medium text-white">创建规则</button>
            </div>

            <div className="mt-6 space-y-4">
              {rules.map((rule) => (
                <article key={rule.title} className="rounded-3xl border border-black/6 bg-[#FBFCFA] p-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-sm uppercase tracking-[0.24em] text-black/35">{rule.title}</p>
                      <h3 className="mt-2 text-2xl font-semibold">{rule.pair}</h3>
                      <p className="mt-3 text-black/60">{rule.condition}</p>
                    </div>
                    <div className="text-right text-sm text-black/50">
                      <p>{rule.cooldown}</p>
                      <p className="mt-2 rounded-full bg-white px-4 py-2 text-black/65">{rule.status}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            <div className="mt-6 rounded-3xl border border-[#E7C36A]/40 bg-[linear-gradient(135deg,rgba(248,239,207,0.58)_0%,rgba(242,217,139,0.52)_100%)] p-6 text-base leading-8 text-black/70">
              通过静默时段和冷却时间控制，提醒会更有价值，不会让页面变成高频噪音墙。
            </div>
          </section>

          <section className="space-y-8">
            <section className="rounded-panel bg-white p-8 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">触发历史</p>
              <h2 className="mt-2 text-3xl font-semibold">提醒时间线</h2>
              <div className="mt-6 space-y-4">
                {historyItems.map((item) => (
                  <article key={item.time} className="rounded-3xl bg-[#F7FAF7] p-5">
                    <p className="text-sm text-black/35">{item.time}</p>
                    <h3 className="mt-2 text-xl font-semibold">{item.title}</h3>
                    <p className="mt-3 leading-7 text-black/60">{item.detail}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="rounded-panel bg-white p-8 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">执行边界</p>
              <h2 className="mt-2 text-3xl font-semibold">风险护栏</h2>
              <p className="mt-6 text-base leading-8 text-black/65">
                这里的自动化只生成提醒通知和参考信号，任何真实换汇操作都仍然需要用户在线下手动完成。
              </p>
            </section>
          </section>
        </section>
      </div>
    </main>
  );
}
