"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { authorizedDemoFetch, ensureDemoAuth } from "../../../lib/demo-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";
const SETTLEMENT_CACHE_KEY = "smartfx_settlement_request";

type SettlementAnalysis = {
  pair: string;
  current_rate: number;
  current_percentile_30d: number;
  current_percentile_90d: number;
  immediate_value: number;
  projected_best_case_value: number;
  estimated_delta: number;
  recommended_window_days: number;
  recommended_window_end_date: string;
  recommended_window_reason: string;
  zone_label: string;
  narrative: string;
  disclaimer: string;
};

export default function ProSettlementPage() {
  const router = useRouter();
  const [amount, setAmount] = useState("50000");
  const [sourceCurrency, setSourceCurrency] = useState("USD");
  const [targetCurrency, setTargetCurrency] = useState("CNY");
  const [arrivalDate, setArrivalDate] = useState("2026-04-25");
  const [optimizationGoal, setOptimizationGoal] = useState<"maximize_income" | "minimize_cost">("maximize_income");
  const [targetRate, setTargetRate] = useState("");
  const [analysis, setAnalysis] = useState<SettlementAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

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
          setError(err instanceof Error ? err.message : "演示身份初始化失败");
        }
      }
    }

    void boot();

    return () => {
      isMounted = false;
    };
  }, []);

  function buildPayload() {
    return {
      amount: Number(amount),
      source_currency: sourceCurrency,
      target_currency: targetCurrency,
      arrival_date: arrivalDate,
      optimization_goal: optimizationGoal,
      target_rate: targetRate ? Number(targetRate) : null,
      latest_settlement_date: null,
    };
  }

  async function submitAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const payload = buildPayload();
      const response = await authorizedDemoFetch(`${API_BASE}/pro/settlement`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`结算分析失败：${response.status}`);
      }

      const result = (await response.json()) as SettlementAnalysis;
      setAnalysis(result);
      window.sessionStorage.setItem(SETTLEMENT_CACHE_KEY, JSON.stringify(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "结算分析失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function generateReport() {
    setIsGenerating(true);
    setError(null);

    try {
      const settlementData = buildPayload();
      window.sessionStorage.setItem(SETTLEMENT_CACHE_KEY, JSON.stringify(settlementData));

      const response = await authorizedDemoFetch(`${API_BASE}/pro/report/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          settlement_data: settlementData,
        }),
      });

      if (!response.ok) {
        throw new Error(`生成结算报告失败：${response.status}`);
      }

      const payload = (await response.json()) as { job_id: string };
      router.push(`/pro/report?jobId=${payload.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成结算报告失败");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#F5F7F4] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1380px] space-y-8">
        <header className="rounded-panel bg-[linear-gradient(135deg,#32B56D_0%,#27A860_100%)] p-8 text-white shadow-soft">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-white/70">专业版结算</p>
              <h1 className="mt-3 text-4xl font-semibold">结算计算器</h1>
              <p className="mt-3 max-w-3xl text-base leading-8 text-white/80">
                输入结算金额、币种、到款日期和优化目标后，可以获得当前区间位置、预计价值、建议观察窗口和 AI 参考说明。
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/pro/report" className="rounded-full bg-white px-5 py-3 text-sm font-medium text-jade-600">
                查看结算报告
              </Link>
              <Link href="/" className="rounded-full border border-white/25 px-5 py-3 text-sm text-white/85">
                返回首页
              </Link>
            </div>
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-[0.92fr_1.08fr]">
          <form className="rounded-panel bg-white p-8 shadow-soft" onSubmit={submitAnalysis}>
            <p className="text-sm uppercase tracking-[0.28em] text-black/40">输入参数</p>
            <h2 className="mt-2 text-3xl font-semibold">结算条件</h2>
            <div className="mt-6 grid gap-5">
              <div>
                <label className="mb-2 block text-sm text-black/45">结算金额</label>
                <input
                  className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none"
                  placeholder="50000"
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                />
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm text-black/45">源币种</label>
                  <select
                    className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none"
                    value={sourceCurrency}
                    onChange={(event) => setSourceCurrency(event.target.value)}
                  >
                    <option value="USD">USD</option>
                    <option value="HKD">HKD</option>
                    <option value="CNY">CNY</option>
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-black/45">目标币种</label>
                  <select
                    className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none"
                    value={targetCurrency}
                    onChange={(event) => setTargetCurrency(event.target.value)}
                  >
                    <option value="CNY">CNY</option>
                    <option value="USD">USD</option>
                    <option value="HKD">HKD</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm text-black/45">预计到款日期</label>
                <input
                  type="date"
                  className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none"
                  value={arrivalDate}
                  onChange={(event) => setArrivalDate(event.target.value)}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-black/45">目标汇率（可选）</label>
                <input
                  className="w-full rounded-2xl border border-black/10 bg-[#F8FAF7] px-4 py-4 outline-none"
                  placeholder="例如 7.2000"
                  value={targetRate}
                  onChange={(event) => setTargetRate(event.target.value)}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-black/45">优化目标</label>
                <div className="flex gap-3">
                  <button
                    className={`rounded-full px-5 py-3 text-sm font-medium ${optimizationGoal === "maximize_income" ? "bg-jade-600 text-white" : "border border-black/10 text-black/65"}`}
                    type="button"
                    onClick={() => setOptimizationGoal("maximize_income")}
                  >
                    最大化结算收益
                  </button>
                  <button
                    className={`rounded-full px-5 py-3 text-sm font-medium ${optimizationGoal === "minimize_cost" ? "bg-jade-600 text-white" : "border border-black/10 text-black/65"}`}
                    type="button"
                    onClick={() => setOptimizationGoal("minimize_cost")}
                  >
                    最小化结算成本
                  </button>
                </div>
              </div>

              {error ? <p className="text-sm text-red-600">{error}</p> : null}

              <div className="flex flex-wrap gap-3">
                <button
                  className="rounded-full bg-[#1C2A4B] px-6 py-4 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={!isReady || isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "分析中..." : "生成结算分析"}
                </button>
                <button
                  className="rounded-full border border-black/10 px-6 py-4 font-medium text-black/70 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={!isReady || isGenerating}
                  type="button"
                  onClick={generateReport}
                >
                  {isGenerating ? "报告生成中..." : "直接生成结算报告"}
                </button>
              </div>
            </div>
          </form>

          <div className="space-y-8">
            <section className="rounded-panel bg-white p-8 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">分析结果</p>
              <h2 className="mt-2 text-3xl font-semibold">结算建议</h2>

              {analysis ? (
                <>
                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    <div className="rounded-3xl bg-[#F7FAF7] p-5">
                      <p className="text-sm text-black/40">当前汇率</p>
                      <p className="mt-2 text-4xl font-semibold">{analysis.current_rate.toFixed(4)}</p>
                    </div>
                    <div className="rounded-3xl bg-[#F7FAF7] p-5">
                      <p className="text-sm text-black/40">建议观察窗口</p>
                      <p className="mt-2 text-4xl font-semibold">{analysis.recommended_window_days} 天</p>
                      <p className="mt-3 text-sm leading-6 text-black/55">
                        观察至 {analysis.recommended_window_end_date}
                      </p>
                    </div>
                    <div className="rounded-3xl bg-[#F7FAF7] p-5">
                      <p className="text-sm text-black/40">立即结算参考值</p>
                      <p className="mt-2 text-4xl font-semibold">{analysis.immediate_value.toFixed(2)}</p>
                    </div>
                    <div className="rounded-3xl bg-[#F7FAF7] p-5">
                      <p className="text-sm text-black/40">潜在参考差额</p>
                      <p className="mt-2 text-4xl font-semibold">{analysis.estimated_delta.toFixed(2)}</p>
                    </div>
                  </div>

                  <div className="mt-6 rounded-3xl border border-[#E7C36A]/40 bg-[linear-gradient(135deg,rgba(248,239,207,0.58)_0%,rgba(242,217,139,0.52)_100%)] p-6 text-base leading-8 text-black/70">
                    {analysis.narrative}
                  </div>

                  <div className="mt-4 rounded-3xl bg-[#FBFCFA] p-5 text-sm leading-7 text-black/65">
                    <span className="font-medium text-black/75">窗口判断：</span>
                    {analysis.recommended_window_reason}
                  </div>

                  <div className="mt-6 grid gap-4 md:grid-cols-3">
                    <div className="rounded-3xl bg-[#FBFCFA] p-5">
                      <p className="text-sm text-black/40">30 天分位</p>
                      <p className="mt-2 text-2xl font-semibold">{analysis.current_percentile_30d.toFixed(2)}%</p>
                    </div>
                    <div className="rounded-3xl bg-[#FBFCFA] p-5">
                      <p className="text-sm text-black/40">90 天分位</p>
                      <p className="mt-2 text-2xl font-semibold">{analysis.current_percentile_90d.toFixed(2)}%</p>
                    </div>
                    <div className="rounded-3xl bg-[#FBFCFA] p-5">
                      <p className="text-sm text-black/40">区间位置</p>
                      <p className="mt-2 text-2xl font-semibold">{analysis.zone_label}</p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="mt-6 rounded-3xl bg-[#F7FAF7] p-6 text-base leading-8 text-black/60">
                  先在左侧填写结算条件，再点击“生成结算分析”，这里会显示结算价值、区间位置和建议观察窗口。
                </div>
              )}
            </section>

            <section className="rounded-panel bg-white p-8 shadow-soft">
              <p className="text-sm uppercase tracking-[0.28em] text-black/40">后续动作</p>
              <h2 className="mt-2 text-3xl font-semibold">结算报告</h2>
              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  className="rounded-full bg-jade-600 px-6 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={!isReady || isGenerating}
                  onClick={generateReport}
                  type="button"
                >
                  {isGenerating ? "生成中..." : "生成 AI 结算报告"}
                </button>
                <Link href="/pro/report" className="rounded-full border border-black/10 px-6 py-3 text-black/70">
                  打开报告页
                </Link>
              </div>
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}
