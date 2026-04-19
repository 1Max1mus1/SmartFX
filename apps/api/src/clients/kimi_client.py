from __future__ import annotations

from collections.abc import Sequence

import httpx

from src.settings import SETTINGS

DISCLAIMER = "以上内容仅供信息参考，不构成任何投资建议。"


class KimiClient:
    def __init__(self) -> None:
        self.provider = SETTINGS.AI.PROVIDER
        self.model = SETTINGS.AI.MODEL
        self.api_key = SETTINGS.AI.API_KEY
        self.base_url = SETTINGS.AI.BASE_URL.rstrip("/")

    async def _chat_completion(self, messages: list[dict], *, max_tokens: int = 1200) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload["choices"][0]["message"]["content"].strip()

    async def generate_daily_report(self, context: dict) -> dict:
        if self.provider == "mock" or not self.api_key:
            summary_markdown = "\n".join(
                [
                    "# 外汇参考分析日报",
                    "",
                    "## 实时汇率",
                    "",
                    "| 货币对 | 汇率 | 24小时变化率 |",
                    "| --- | ---: | ---: |",
                    f"| USD/CNY | {context['live_map']['USD/CNY']['rate']} | {context['live_map']['USD/CNY']['change_pct_24h']}% |",
                    f"| HKD/CNY | {context['live_map']['HKD/CNY']['rate']} | {context['live_map']['HKD/CNY']['change_pct_24h']}% |",
                    f"| USD/HKD | {context['live_map']['USD/HKD']['rate']} | {context['live_map']['USD/HKD']['change_pct_24h']}% |",
                    "",
                    "## 信号判断",
                    "",
                    f"- USD/CNY：{context['signals']['USD/CNY']['label']}",
                    f"- HKD/CNY：{context['signals']['HKD/CNY']['label']}",
                    f"- USD/HKD：{context['signals']['USD/HKD']['label']}",
                    "",
                    "## 趋势摘要",
                    "",
                    context["trend_summary"],
                    "",
                    "## 市场关注点",
                    "",
                    *[f"- {headline}" for headline in context["news_headlines"]],
                    "",
                    "## 换汇参考",
                    "",
                    f"- {context['reference_signal']}",
                    "",
                    DISCLAIMER,
                ]
            )
        else:
            system_prompt = (
                "你是 SmartFX 的外汇分析助手。请根据提供的汇率、信号、统计数据和新闻线索，"
                "输出一份中文 Markdown 日报。语气要专业、清晰、克制，不要写成投资承诺。"
                f"最后必须保留这句提示：{DISCLAIMER}"
            )
            user_prompt = (
                f"实时汇率：{context['live_map']}\n"
                f"统计数据：{context['stats_map']}\n"
                f"信号：{context['signals']}\n"
                f"趋势摘要：{context['trend_summary']}\n"
                f"新闻线索：{context['news_headlines']}\n"
                f"换汇参考：{context['reference_signal']}"
            )
            try:
                summary_markdown = await self._chat_completion(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=1400,
                )
                if DISCLAIMER not in summary_markdown:
                    summary_markdown = f"{summary_markdown}\n\n{DISCLAIMER}"
            except Exception:
                summary_markdown = "\n".join(
                    [
                        "# 外汇参考分析日报",
                        "",
                        "## 系统提示",
                        "",
                        "- 当前真实 AI 服务暂时不可用，已切换到基础日报模式。",
                        "",
                        DISCLAIMER,
                    ]
                )

        return {
            "summary_markdown": summary_markdown,
            "signals": {
                "signal_usd_cny": context["signals"]["USD/CNY"]["signal"],
                "signal_hkd_cny": context["signals"]["HKD/CNY"]["signal"],
                "signal_usd_hkd": context["signals"]["USD/HKD"]["signal"],
            },
        }

    async def chat(self, prompt: str, context: dict, history: Sequence[dict]) -> str:
        if self.provider == "mock" or not self.api_key:
            latest_signal = context["daily_report_signal"]
            recent_records = context["record_summary"]
            return "\n".join(
                [
                    "我会结合当前汇率位置、区间信号和你的换汇背景给出参考说明。",
                    f"当前主信号偏向：{latest_signal}。",
                    f"你最近的参考记录数量：{recent_records['count']} 笔，累计基准金额约 {recent_records['base_amount']}。",
                    "如果这笔换汇属于刚需，通常更适合优先考虑执行节奏和到账时间，而不是只盯一个点位。",
                    DISCLAIMER,
                ]
            )

        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "你是 SmartFX 的 AI 换汇助手。请提供克制、清晰、偏执行层的参考意见，"
                    "不要给出保本、保收益、稳赚等表达。"
                    f"回答结尾必须保留：{DISCLAIMER}"
                ),
            }
        ]
        messages.extend(history)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"用户问题：{prompt}\n"
                    f"今日主信号：{context['daily_report_signal']}\n"
                    f"区间统计：{context['stats_map']}\n"
                    f"用户记录摘要：{context['record_summary']}"
                ),
            }
        )

        try:
            answer = await self._chat_completion(messages, max_tokens=1200)
            if DISCLAIMER not in answer:
                answer = f"{answer}\n\n{DISCLAIMER}"
            return answer
        except Exception:
            return f"当前真实 AI 服务暂时不可用，请稍后重试。\n\n{DISCLAIMER}"

    async def generate_settlement_report(self, analysis: dict, request: dict) -> dict:
        if self.provider == "mock" or not self.api_key:
            title = "SmartFX AI 结算分析报告"
            summary = (
                f"本次结算场景为 {request['amount']} {request['source_currency']} 兑换到 {request['target_currency']}，"
                f"当前参考汇率为 {analysis['current_rate']:.4f}，立即结算的参考价值约为 {analysis['immediate_value']:.2f}。"
            )
            sections = [
                f"当前区间位置为 {analysis['zone_label']}，建议先结合 {analysis['recommended_window_days']} 天观察窗口安排执行。",
                f"若等待更优窗口，历史区间推演下的最佳参考值约为 {analysis['projected_best_case_value']:.2f}，与立即执行相比差额约 {analysis['estimated_delta']:.2f}。",
                DISCLAIMER,
            ]
            markdown_report = "\n".join(
                [
                    f"# {title}",
                    "",
                    "## 摘要",
                    "",
                    summary,
                    "",
                    "## 关键结论",
                    "",
                    *[f"- {item}" for item in sections],
                ]
            )
            return {
                "title": title,
                "summary": summary,
                "sections": sections,
                "markdown_report": markdown_report,
            }

        prompt = (
            "请根据下面的结算分析数据，输出一份中文 Markdown 结算报告。"
            "内容需要包括：标题、摘要、三条关键建议和风险提示。"
            "不要写成收益承诺，不要使用夸张措辞。"
            f"结尾必须保留：{DISCLAIMER}\n"
            f"请求参数：{request}\n"
            f"分析数据：{analysis}"
        )
        try:
            markdown_report = await self._chat_completion(
                [
                    {"role": "system", "content": "你是 SmartFX 的专业结算分析助手。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
            )
            if DISCLAIMER not in markdown_report:
                markdown_report = f"{markdown_report}\n\n{DISCLAIMER}"
        except Exception:
            markdown_report = "\n".join(
                [
                    "# SmartFX AI 结算分析报告",
                    "",
                    "## 摘要",
                    "",
                    "当前真实 AI 结算报告服务暂时不可用，已切换到基础报告模式。",
                    "",
                    DISCLAIMER,
                ]
            )

        lines = [line.strip("- ").strip() for line in markdown_report.splitlines() if line.strip()]
        summary = lines[2] if len(lines) > 2 else "暂无可用摘要。"
        sections = [line for line in lines if line and line != summary][:4]
        return {
            "title": "SmartFX AI 结算分析报告",
            "summary": summary,
            "sections": sections,
            "markdown_report": markdown_report,
        }
