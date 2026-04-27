"use client";

import { FormEvent, useState } from "react";

import { authorizedDemoFetch } from "../lib/demo-auth";
import { MarkdownContent } from "./markdown-content";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";

type StudentPaymentAdvicePayload = {
  decision: string;
  decision_level: "pay_now" | "split_now" | "watch_short";
  decision_reason: string;
  rate_assessment: string;
  deadline_pressure: string;
  suggested_action: string;
  split_payment_plan: string | null;
  market_snapshot: {
    requested_pair: string;
    reference_pair: string;
    current_rate: number;
    reference_rate: number;
    change_pct_24h: number;
    percentile_30d: number;
    percentile_90d: number;
    favorable_score_30d: number;
    favorable_score_90d: number;
  };
  analysis_markdown: string;
  disclaimer: string;
};

type StudentPaymentAdvisorCardProps = {
  isReady: boolean;
  onUseFollowUp: (message: string) => void;
};

function formatDateOffset(days: number) {
  const nextDate = new Date();
  nextDate.setDate(nextDate.getDate() + days);
  return nextDate.toISOString().slice(0, 10);
}

function formatRate(rate: number) {
  return rate >= 1 ? rate.toFixed(4) : rate.toFixed(6);
}

export function StudentPaymentAdvisorCard({ isReady, onUseFollowUp }: StudentPaymentAdvisorCardProps) {
  const [deadlineDate, setDeadlineDate] = useState(formatDateOffset(7));
  const [amount, setAmount] = useState("20000");
  const [sourceCurrency, setSourceCurrency] = useState("CNY");
  const [targetCurrency, setTargetCurrency] = useState("USD");
  const [canSplitPayment, setCanSplitPayment] = useState(true);
  const [riskPreference, setRiskPreference] = useState<"stable" | "balanced" | "opportunistic">("balanced");
  const [notes, setNotes] = useState("如果有必要，我可以分两次操作。");
  const [result, setResult] = useState<StudentPaymentAdvicePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submitAdvice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await authorizedDemoFetch(`${API_BASE}/ai/student-payment-advice`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          deadline_date: deadlineDate,
          amount: amount.trim() ? Number(amount) : null,
          source_currency: sourceCurrency,
          target_currency: targetCurrency,
          can_split_payment: canSplitPayment,
          risk_preference: riskPreference,
          notes: notes.trim() || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Student payment advice request failed: ${response.status}`);
      }

      const payload = (await response.json()) as StudentPaymentAdvicePayload;
      setResult(payload);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Student payment advice request failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  function useFollowUpPrompt() {
    if (!result) {
      return;
    }

    const followUp = [
      "我刚拿到一条留学生缴费建议。",
      `建议结论：${result.decision}`,
      `核心原因：${result.decision_reason}`,
      `当前汇率位置：${result.market_snapshot.requested_pair} 位于近 30 天 ${result.market_snapshot.percentile_30d.toFixed(2)}% 的位置。`,
      "请你进一步解释为什么这样安排，并告诉我如果我只能操作一次，应该怎么做。",
    ].join("\n");

    onUseFollowUp(followUp);
  }

  return (
    <section className="rounded-panel bg-white p-8 shadow-soft">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-black/40">Student Scenario</p>
          <h2 className="mt-2 text-3xl font-semibold">留学生缴费助手</h2>
          <p className="mt-3 max-w-2xl text-base leading-8 text-black/60">
            输入缴费截止日期、换汇方向，以及是否接受分批支付。系统会结合当前汇率位置和时间压力，给出更贴近真实操作的执行建议。
          </p>
        </div>
        <div className="rounded-3xl bg-[linear-gradient(135deg,rgba(248,239,207,0.72)_0%,rgba(242,217,139,0.56)_100%)] px-5 py-4 text-sm leading-7 text-black/70">
          <p className="font-medium text-black/80">适用范围</p>
          <p>当前只支持 USD、HKD、CNY，输出的是缴费参考建议，不构成投资建议。</p>
        </div>
      </div>

      <div className="mt-8 grid gap-8 2xl:grid-cols-[0.92fr_1.08fr]">
        <form className="rounded-[28px] border border-black/8 bg-[#FBFCFA] p-5" onSubmit={submitAdvice}>
          <div className="grid gap-5">
            <div>
              <label className="mb-2 block text-sm text-black/45">缴费截止日期</label>
              <input
                type="date"
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-4 outline-none"
                value={deadlineDate}
                onChange={(event) => setDeadlineDate(event.target.value)}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm text-black/45">缴费金额（可选）</label>
              <input
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-4 outline-none"
                placeholder="例如 20000"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm text-black/45">资金来源币种</label>
                <select
                  className="w-full rounded-2xl border border-black/10 bg-white px-4 py-4 outline-none"
                  value={sourceCurrency}
                  onChange={(event) => setSourceCurrency(event.target.value)}
                >
                  <option value="CNY">CNY</option>
                  <option value="USD">USD</option>
                  <option value="HKD">HKD</option>
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm text-black/45">目标支付币种</label>
                <select
                  className="w-full rounded-2xl border border-black/10 bg-white px-4 py-4 outline-none"
                  value={targetCurrency}
                  onChange={(event) => setTargetCurrency(event.target.value)}
                >
                  <option value="USD">USD</option>
                  <option value="HKD">HKD</option>
                  <option value="CNY">CNY</option>
                </select>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm text-black/45">风险偏好</label>
              <div className="flex flex-wrap gap-3">
                {[
                  { value: "stable", label: "求稳优先" },
                  { value: "balanced", label: "平衡处理" },
                  { value: "opportunistic", label: "愿意短等" },
                ].map((item) => (
                  <button
                    key={item.value}
                    className={`rounded-full px-5 py-3 text-sm font-medium ${
                      riskPreference === item.value ? "bg-jade-600 text-white" : "border border-black/10 text-black/65"
                    }`}
                    type="button"
                    onClick={() => setRiskPreference(item.value as "stable" | "balanced" | "opportunistic")}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm text-black/45">是否接受分批支付</label>
              <div className="flex gap-3">
                <button
                  className={`rounded-full px-5 py-3 text-sm font-medium ${
                    canSplitPayment ? "bg-[#1C2A4B] text-white" : "border border-black/10 text-black/65"
                  }`}
                  type="button"
                  onClick={() => setCanSplitPayment(true)}
                >
                  可以分批
                </button>
                <button
                  className={`rounded-full px-5 py-3 text-sm font-medium ${
                    !canSplitPayment ? "bg-[#1C2A4B] text-white" : "border border-black/10 text-black/65"
                  }`}
                  type="button"
                  onClick={() => setCanSplitPayment(false)}
                >
                  只能一次
                </button>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm text-black/45">补充说明（可选）</label>
              <textarea
                className="min-h-[120px] w-full rounded-2xl border border-black/10 bg-white px-4 py-4 outline-none"
                placeholder="例如：学费最晚周五前必须到账，或者家里这周只能操作一次。"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
              />
            </div>

            {error ? <p className="text-sm text-red-600">{error}</p> : null}

            <div className="flex flex-wrap gap-3">
              <button
                className="rounded-full bg-jade-600 px-6 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!isReady || isSubmitting}
                type="submit"
              >
                {isSubmitting ? "生成建议中..." : "生成缴费建议"}
              </button>
              <button
                className="rounded-full border border-black/10 px-6 py-3 font-medium text-black/70"
                type="button"
                onClick={() => {
                  setDeadlineDate(formatDateOffset(4));
                  setAmount("18000");
                  setSourceCurrency("CNY");
                  setTargetCurrency("USD");
                  setCanSplitPayment(true);
                  setRiskPreference("balanced");
                  setNotes("学费这周内要交，如果有必要我可以分两次操作。");
                }}
              >
                填入示例
              </button>
            </div>
          </div>
        </form>

        <div className="space-y-5">
          {result ? (
            <>
            <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl bg-[linear-gradient(135deg,rgba(248,239,207,0.72)_0%,rgba(242,217,139,0.56)_100%)] p-5">
                  <p className="text-sm text-black/45">今日建议</p>
                  <p className="mt-2 text-2xl font-semibold text-black/85">{result.decision}</p>
                  <p className="mt-3 text-sm leading-7 text-black/70">{result.decision_reason}</p>
                </div>
                <div className="rounded-3xl bg-[#F7FAF7] p-5">
                  <p className="text-sm text-black/45">操作建议</p>
                  <p className="mt-2 text-base leading-8 text-black/75">{result.suggested_action}</p>
                  {result.split_payment_plan ? <p className="mt-3 text-sm leading-7 text-black/60">{result.split_payment_plan}</p> : null}
                </div>
              </div>

            <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
                <div className="rounded-3xl bg-white p-5 shadow-soft">
                  <p className="text-sm text-black/40">当前方向</p>
                  <p className="mt-2 text-2xl font-semibold">{result.market_snapshot.requested_pair}</p>
                </div>
                <div className="rounded-3xl bg-white p-5 shadow-soft">
                  <p className="text-sm text-black/40">当前汇率</p>
                  <p className="mt-2 text-2xl font-semibold">{formatRate(result.market_snapshot.current_rate)}</p>
                </div>
                <div className="rounded-3xl bg-white p-5 shadow-soft">
                  <p className="text-sm text-black/40">30 天位置</p>
                  <p className="mt-2 text-2xl font-semibold">{result.market_snapshot.percentile_30d.toFixed(2)}%</p>
                  <p className="mt-2 text-sm text-black/55">{result.rate_assessment}</p>
                </div>
                <div className="rounded-3xl bg-white p-5 shadow-soft">
                  <p className="text-sm text-black/40">截止压力</p>
                  <p className="mt-2 text-2xl font-semibold">{result.deadline_pressure}</p>
                  <p className="mt-2 text-sm text-black/55">90 天位置 {result.market_snapshot.percentile_90d.toFixed(2)}%</p>
                </div>
              </div>

              <div className="rounded-3xl border border-[#E7C36A]/40 bg-[#FFF9E8] p-6">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm uppercase tracking-[0.18em] text-black/40">Deep Analysis</p>
                    <h3 className="mt-2 text-2xl font-semibold">AI 解释</h3>
                  </div>
                  <button
                    className="rounded-full bg-[#1C2A4B] px-5 py-3 text-sm font-medium text-white"
                    type="button"
                    onClick={useFollowUpPrompt}
                  >
                    带入聊天继续追问
                  </button>
                </div>
                <MarkdownContent content={result.analysis_markdown} className="text-black/75" />
              </div>
            </>
          ) : (
            <div className="rounded-3xl bg-[#F7FAF7] p-6 text-base leading-8 text-black/60">
              先填写缴费信息，再生成建议。结果会告诉你今天是否适合支付、当前汇率在最近区间里处于什么位置，以及是否值得分批处理。
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
