"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MarkdownContent } from "../../components/markdown-content";
import { authorizedDemoFetch, ensureDemoAuth } from "../../lib/demo-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";

type RateSnapshot = {
  pairs: Array<{
    pair: string;
    rate: number;
    change_pct_24h: number;
    source: string;
    updated_at: string;
  }>;
};

type ReportPayload = {
  report_date: string;
  generated_at: string;
  summary_markdown: string;
  signal_usd_cny: string;
  signal_hkd_cny: string;
  signal_usd_hkd: string;
  rates_snapshot: RateSnapshot;
};

const signalLabelMap: Record<string, string> = {
  buy: "买入参考",
  hold: "继续观察",
  sell: "卖出参考",
};

export default function ReportPage() {
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadReport() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await authorizedDemoFetch(`${API_BASE}/report/daily`);

        if (!response.ok) {
          throw new Error(`AI 简报加载失败：${response.status}`);
        }

        const payload = (await response.json()) as ReportPayload;
        if (isMounted) {
          setReport(payload);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "AI 简报加载失败");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadReport();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="min-h-screen bg-[#F5F7F4] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1320px] space-y-8">
        <header className="rounded-panel bg-[linear-gradient(135deg,#F8EFCF_0%,#F2D98B_100%)] p-8 shadow-soft">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-black/40">AI 每日简报</p>
              <h1 className="mt-3 text-4xl font-semibold">今日汇率分析</h1>
              <p className="mt-3 max-w-3xl text-base leading-8 text-black/60">
                页面会直接调用后端接口，展示今日 AI 汇率摘要、表格、信号判断和实时汇率快照。
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/" className="rounded-full border border-black/10 px-5 py-3 text-sm text-black/70">
                返回首页
              </Link>
              <Link href="/assistant" className="rounded-full bg-jade-600 px-5 py-3 text-sm font-medium text-white">
                打开 AI 对话
              </Link>
            </div>
          </div>
        </header>

        {isLoading ? (
          <section className="rounded-panel bg-white p-8 shadow-soft">
            <p className="text-base text-black/60">正在生成 AI 简报...</p>
          </section>
        ) : null}

        {error ? (
          <section className="rounded-panel bg-white p-8 shadow-soft">
            <p className="text-base text-red-600">{error}</p>
          </section>
        ) : null}

        {report ? (
          <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="rounded-panel bg-white p-8 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">今日内容</p>
              <h2 className="mt-2 text-3xl font-semibold">摘要正文</h2>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-black/45">
                <span>日期：{report.report_date}</span>
                <span>生成时间：{new Date(report.generated_at).toLocaleString("zh-CN")}</span>
              </div>

              <div className="mt-6 rounded-3xl bg-[linear-gradient(135deg,rgba(248,239,207,0.6)_0%,rgba(242,217,139,0.55)_100%)] p-6">
                <MarkdownContent content={report.summary_markdown} />
              </div>
            </div>

            <aside className="space-y-6">
              <section className="rounded-panel bg-white p-8 shadow-soft">
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">信号概览</p>
                <h2 className="mt-2 text-3xl font-semibold">当前判断</h2>
                <div className="mt-6 space-y-4">
                  {[
                    ["USD/CNY", report.signal_usd_cny],
                    ["HKD/CNY", report.signal_hkd_cny],
                    ["USD/HKD", report.signal_usd_hkd],
                  ].map(([pair, signal]) => (
                    <div key={pair} className="rounded-3xl bg-[#F7FAF7] p-5">
                      <p className="text-sm text-black/40">{pair}</p>
                      <p className="mt-2 text-2xl font-semibold">{signalLabelMap[signal] ?? signal}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-panel bg-white p-8 shadow-soft">
                <p className="text-sm uppercase tracking-[0.28em] text-black/40">实时汇率</p>
                <h2 className="mt-2 text-3xl font-semibold">汇率快照</h2>
                <div className="mt-6 space-y-4">
                  {report.rates_snapshot.pairs.map((item) => (
                    <article key={item.pair} className="rounded-3xl border border-black/6 bg-[#FBFCFA] p-5">
                      <div className="flex items-end justify-between gap-4">
                        <div>
                          <p className="text-xl font-semibold">{item.pair}</p>
                          <p className="mt-1 text-sm text-black/45">{item.source === "exchange-rate-api" ? "汇率接口" : item.source}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-3xl font-semibold">{item.rate.toFixed(4)}</p>
                          <p className="mt-1 text-sm text-black/45">{item.change_pct_24h.toFixed(2)}%</p>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </aside>
          </section>
        ) : null}
      </div>
    </main>
  );
}
