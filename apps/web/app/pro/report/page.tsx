"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { MarkdownContent } from "../../../components/markdown-content";
import { ensureDemoAuth } from "../../../lib/demo-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010/api";
const SETTLEMENT_CACHE_KEY = "smartfx_settlement_request";

type ReportResult = {
  title: string;
  summary: string;
  sections: string[];
  markdown_report?: string;
  analysis?: {
    pair: string;
    current_rate: number;
    current_percentile_30d: number;
    current_percentile_90d: number;
    immediate_value: number;
    projected_best_case_value: number;
    estimated_delta: number;
    recommended_window_days: number;
    zone_label: string;
    narrative: string;
    disclaimer: string;
  };
};

type ReportStatusPayload = {
  job_id: string;
  job_status: string;
  result: ReportResult | null;
  error_message: string | null;
  updated_at: string;
};

const statusLabelMap: Record<string, string> = {
  idle: "未开始",
  pending: "排队中",
  running: "生成中",
  done: "已完成",
  failed: "失败",
};

function ProReportContent() {
  const searchParams = useSearchParams();
  const [jobId, setJobId] = useState<string | null>(searchParams.get("jobId"));
  const [jobStatus, setJobStatus] = useState<string>("idle");
  const [reportResult, setReportResult] = useState<ReportResult | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
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

  useEffect(() => {
    if (!jobId || !isReady) {
      return;
    }

    let cancelled = false;

    async function pollJob() {
      try {
        const { token } = await ensureDemoAuth();

        for (let attempt = 0; attempt < 8; attempt += 1) {
          const response = await fetch(`${API_BASE}/pro/report/status/${jobId}`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error(`获取报告状态失败：${response.status}`);
          }

          const payload = (await response.json()) as ReportStatusPayload;
          if (cancelled) {
            return;
          }

          setJobStatus(payload.job_status);
          setReportResult(payload.result);
          setUpdatedAt(payload.updated_at);
          setError(payload.error_message);

          if (payload.job_status === "done" || payload.job_status === "failed") {
            return;
          }

          await new Promise((resolve) => setTimeout(resolve, 1200));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "获取报告状态失败");
        }
      }
    }

    void pollJob();

    return () => {
      cancelled = true;
    };
  }, [jobId, isReady]);

  async function generateFromCachedRequest() {
    setIsGenerating(true);
    setError(null);

    try {
      const cached = window.sessionStorage.getItem(SETTLEMENT_CACHE_KEY);
      if (!cached) {
        throw new Error("没有找到最近一次结算参数，请先去结算计算器生成分析。");
      }

      const { token } = await ensureDemoAuth();
      const response = await fetch(`${API_BASE}/pro/report/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          settlement_data: JSON.parse(cached),
        }),
      });

      if (!response.ok) {
        throw new Error(`生成结算报告失败：${response.status}`);
      }

      const payload = (await response.json()) as { job_id: string; job_status: string };
      setJobId(payload.job_id);
      setJobStatus(payload.job_status);
      setUpdatedAt(null);
      setReportResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成结算报告失败");
    } finally {
      setIsGenerating(false);
    }
  }

  const fallbackMarkdown = reportResult
    ? `# ${reportResult.title}\n\n## 摘要\n\n${reportResult.summary}\n\n## 关键要点\n\n${reportResult.sections.map((item) => `- ${item}`).join("\n")}`
    : "";

  const renderedMarkdown = reportResult?.markdown_report || fallbackMarkdown;

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#32B56D_0%,#27A860_100%)] px-6 py-10 text-ink lg:px-10">
      <div className="mx-auto max-w-[1380px] space-y-8">
        <header className="rounded-panel bg-white/95 p-8 shadow-soft">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-black/40">专业版结算报告</p>
              <h1 className="mt-3 text-4xl font-semibold">AI 结算报告</h1>
              <p className="mt-3 max-w-3xl text-base leading-8 text-black/60">
                这里展示结算报告任务状态、正式报告正文，以及结算分析中的关键指标。你可以从结算计算器跳转过来，也可以在这里重新生成。
              </p>
            </div>
            <div className="flex gap-3">
              <Link href="/pro/settlement" className="rounded-full border border-black/10 px-5 py-3 text-sm text-black/70">
                返回结算计算器
              </Link>
              <Link href="/" className="rounded-full bg-jade-600 px-5 py-3 text-sm font-medium text-white">
                返回首页
              </Link>
            </div>
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-[0.76fr_1.24fr]">
          <aside className="rounded-panel bg-white p-8 shadow-soft">
            <p className="text-sm uppercase tracking-[0.28em] text-black/40">任务状态</p>
            <h2 className="mt-2 text-3xl font-semibold">报告进度</h2>
            <div className="mt-6 space-y-4">
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">任务编号</p>
                <p className="mt-2 font-display text-xl font-semibold">{jobId ?? "尚未生成"}</p>
              </div>
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">当前状态</p>
                <p className="mt-2 text-3xl font-semibold text-jade-600">{statusLabelMap[jobStatus] ?? jobStatus}</p>
              </div>
              <div className="rounded-3xl bg-[#F7FAF7] p-5">
                <p className="text-sm text-black/40">最近更新时间</p>
                <p className="mt-2 text-lg font-semibold">{updatedAt ? new Date(updatedAt).toLocaleString("zh-CN") : "等待生成"}</p>
              </div>
              <div className="rounded-3xl border border-[#E7C36A]/40 p-5 text-sm leading-7 text-black/60">
                报告生成是异步任务，通常几秒内会完成。如果你还没有生成过结算分析，可以先去结算计算器填写参数。
              </div>
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
              <button
                className="rounded-full bg-[#1C2A4B] px-6 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!isReady || isGenerating}
                onClick={generateFromCachedRequest}
                type="button"
              >
                {isGenerating ? "生成中..." : "重新生成报告"}
              </button>
            </div>
          </aside>

          <article className="rounded-panel bg-white p-8 shadow-soft">
            <p className="text-sm uppercase tracking-[0.28em] text-black/40">报告正文</p>
            <h2 className="mt-2 text-3xl font-semibold">正式报告</h2>

            {reportResult ? (
              <div className="mt-6 space-y-6">
                <section className="rounded-3xl bg-[linear-gradient(135deg,rgba(248,239,207,0.5)_0%,rgba(242,217,139,0.42)_100%)] p-6">
                  <MarkdownContent content={renderedMarkdown} />
                </section>

                {reportResult.analysis ? (
                  <section className="rounded-3xl bg-[#FBFCFA] p-6">
                    <h3 className="text-xl font-semibold">分析指标</h3>
                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-sm text-black/40">币种对</p>
                        <p className="mt-2 text-2xl font-semibold">{reportResult.analysis.pair}</p>
                      </div>
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-sm text-black/40">当前汇率</p>
                        <p className="mt-2 text-2xl font-semibold">{reportResult.analysis.current_rate.toFixed(4)}</p>
                      </div>
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-sm text-black/40">30 天分位</p>
                        <p className="mt-2 text-2xl font-semibold">{reportResult.analysis.current_percentile_30d.toFixed(2)}%</p>
                      </div>
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-sm text-black/40">90 天分位</p>
                        <p className="mt-2 text-2xl font-semibold">{reportResult.analysis.current_percentile_90d.toFixed(2)}%</p>
                      </div>
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-sm text-black/40">立即结算参考值</p>
                        <p className="mt-2 text-2xl font-semibold">{reportResult.analysis.immediate_value.toFixed(2)}</p>
                      </div>
                      <div className="rounded-2xl bg-white p-4">
                        <p className="text-sm text-black/40">潜在参考差额</p>
                        <p className="mt-2 text-2xl font-semibold">{reportResult.analysis.estimated_delta.toFixed(2)}</p>
                      </div>
                    </div>

                    <div className="mt-6 rounded-3xl border border-[#E7C36A]/40 bg-white p-5 text-base leading-8 text-black/70">
                      {reportResult.analysis.narrative}
                    </div>
                  </section>
                ) : null}
              </div>
            ) : (
              <div className="mt-6 rounded-3xl bg-[#FBFCFA] p-6 text-base leading-8 text-black/60">
                目前还没有可展示的结算报告。你可以点击左侧“重新生成报告”，或者先去结算计算器生成一次分析。
              </div>
            )}
          </article>
        </section>
      </div>
    </main>
  );
}

export default function ProReportPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[linear-gradient(180deg,#32B56D_0%,#27A860_100%)] px-6 py-10 text-ink lg:px-10">
          <div className="mx-auto max-w-[1380px] rounded-panel bg-white/95 p-8 shadow-soft">
            <p className="text-base text-black/60">正在加载结算报告页面...</p>
          </div>
        </main>
      }
    >
      <ProReportContent />
    </Suspense>
  );
}
