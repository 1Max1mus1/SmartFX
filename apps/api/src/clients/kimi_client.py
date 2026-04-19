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

    def _settlement_business_impact(self, analysis: dict, request: dict) -> dict:
        impact_direction = "利润增厚" if request["optimization_goal"] == "maximize_income" else "成本压降"
        immediate_value = analysis["immediate_value"]
        estimated_delta = analysis["estimated_delta"]
        return {
            "impact_direction": impact_direction,
            "immediate_value": immediate_value,
            "projected_best_case_value": analysis["projected_best_case_value"],
            "estimated_delta": estimated_delta,
            "delta_ratio_pct": round((estimated_delta / immediate_value) * 100, 4) if immediate_value else 0.0,
        }

    def _infer_settlement_scenario(self, request: dict) -> dict:
        source_currency = request["source_currency"]
        target_currency = request["target_currency"]
        optimization_goal = request["optimization_goal"]

        if target_currency == "CNY" and source_currency in {"USD", "HKD"}:
            return {
                "scenario_name": "出口收汇",
                "focus_metric": "回款折算人民币金额与利润空间",
                "management_action": "同步评估报价毛利、回款折算和预算达成情况",
            }

        if source_currency == "CNY" and target_currency in {"USD", "HKD"}:
            return {
                "scenario_name": "进口付汇",
                "focus_metric": "采购付汇成本与预算消耗",
                "management_action": "同步评估采购成本、付款窗口和现金流安排",
            }

        if optimization_goal == "maximize_income":
            return {
                "scenario_name": "外币资产结汇",
                "focus_metric": "结汇收入与利润释放",
                "management_action": "同步评估结汇收益兑现节奏和资金回笼效率",
            }

        return {
            "scenario_name": "跨币种支付",
            "focus_metric": "支付成本与预算偏差",
            "management_action": "同步评估成本控制、付款计划和预算偏差",
        }

    def _build_daily_report_fallback(self, context: dict, *, ai_unavailable: bool) -> str:
        system_hint = []
        if ai_unavailable:
            system_hint = [
                "## 系统提示",
                "",
                "- 当前真实 AI 服务暂时不可用，已切换到基础日报模式。",
                "",
            ]

        return "\n".join(
            [
                "# 外汇参考分析日报",
                "",
                *system_hint,
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

    def _build_chat_fallback(self, context: dict, *, ai_unavailable: bool) -> str:
        recent_records = context["record_summary"]
        prefix = []
        if ai_unavailable:
            prefix = ["当前真实 AI 服务暂时不可用，以下为基础参考建议。", ""]

        return "\n".join(
            [
                *prefix,
                "我会结合当前汇率位置、区间信号和你的换汇背景给出参考说明。",
                f"当前主信号偏向：{context['daily_report_signal']}。",
                f"你最近的参考记录数量：{recent_records['count']} 笔，累计基准金额约 {recent_records['base_amount']}。",
                "如果这笔换汇属于刚需，通常更适合优先考虑执行节奏和到账时间，而不是只盯一个点位。",
                DISCLAIMER,
            ]
        )

    def _build_settlement_report_fallback(self, analysis: dict, request: dict, *, ai_unavailable: bool) -> dict:
        business_impact = self._settlement_business_impact(analysis, request)
        scenario = self._infer_settlement_scenario(request)
        title = "SmartFX AI 结算分析报告"
        summary = (
            f"本次结算场景为 {scenario['scenario_name']}，即 {request['amount']} {request['source_currency']} 兑换到 {request['target_currency']}，"
            f"当前参考汇率为 {analysis['current_rate']:.4f}，立即结算的参考价值约为 {analysis['immediate_value']:.2f}。"
            f"若等待更优窗口，对{business_impact['impact_direction']}的参考改善约为 {business_impact['estimated_delta']:.2f}，"
            f"约占本次结算金额的 {business_impact['delta_ratio_pct']:.2f}%，应重点关注{scenario['focus_metric']}。"
        )
        sections = [
            f"商业影响：当前立即结算参考值约为 {business_impact['immediate_value']:.2f}，更优窗口下可能达到 {business_impact['projected_best_case_value']:.2f}，两者差额约为 {business_impact['estimated_delta']:.2f}，可视为本次结算对{scenario['focus_metric']}的浮动区间。",
            f"执行建议：当前区间位置为 {analysis['zone_label']}，建议结合 {analysis['recommended_window_days']} 天观察窗口、到账时间和资金安排来执行。",
            f"经营提示：建议把 {business_impact['estimated_delta']:.2f} {request['target_currency']} 视为经营敏感差额，{scenario['management_action']}。",
            analysis["narrative"],
        ]
        if ai_unavailable:
            sections.insert(0, "当前真实 AI 结算报告服务暂时不可用，已切换到基础报告模式。")
        sections.append(DISCLAIMER)

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

    def _extract_summary_sections(self, markdown_report: str) -> tuple[str, list[str]]:
        lines = [line.strip() for line in markdown_report.splitlines() if line.strip()]
        content_lines = [line.lstrip("- ").strip() for line in lines if not line.startswith("#")]

        summary = next((line for line in content_lines if line != "摘要" and line != "关键结论"), "暂无可用摘要。")
        sections = [line for line in content_lines if line not in {"摘要", "关键结论", summary}]
        return summary, sections[:4]

    async def generate_daily_report(self, context: dict) -> dict:
        if self.provider == "mock" or not self.api_key:
            summary_markdown = self._build_daily_report_fallback(context, ai_unavailable=False)
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
                summary_markdown = self._build_daily_report_fallback(context, ai_unavailable=True)

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
            return self._build_chat_fallback(context, ai_unavailable=False)

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
            return self._build_chat_fallback(context, ai_unavailable=True)

    async def generate_settlement_report(self, analysis: dict, request: dict) -> dict:
        if self.provider == "mock" or not self.api_key:
            return self._build_settlement_report_fallback(analysis, request, ai_unavailable=False)

        business_impact = self._settlement_business_impact(analysis, request)
        scenario = self._infer_settlement_scenario(request)
        prompt = (
            "请根据下面的结算分析数据，输出一份中文 Markdown 结算报告。"
            f"这份报告要面向业务负责人、财务或结算负责人，当前场景更接近“{scenario['scenario_name']}”。"
            "重点解释外汇结算如何影响利润、成本、回款折算金额、报价和预算，而不是只做汇率点评。"
            "内容需要包括：标题、摘要、商业影响、执行建议、风险提示。"
            "请优先量化说明立即结算与等待更优窗口之间的金额差额、占比，以及对经营数据的意义。"
            f"请尤其围绕“{scenario['focus_metric']}”展开，并在建议里体现“{scenario['management_action']}”。"
            "不要写成收益承诺，不要使用夸张措辞。"
            f"结尾必须保留：{DISCLAIMER}\n"
            f"请求参数：{request}\n"
            f"分析数据：{analysis}\n"
            f"商业影响量化参考：{business_impact}\n"
            f"业务场景参考：{scenario}"
        )
        try:
            markdown_report = await self._chat_completion(
                [
                    {
                        "role": "system",
                        "content": (
                            "你是 SmartFX 的专业结算分析助手。"
                            "你的重点是把汇率变化对业务利润、成本、回款折算、报价和预算的影响说清楚，"
                            "并给出可执行的结算建议。请多使用金额、差额、占比来支撑结论。"
                            "如果是出口收汇，就多讲回款折算和利润释放；如果是进口付汇，就多讲采购成本和预算消耗。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
            )
            if DISCLAIMER not in markdown_report:
                markdown_report = f"{markdown_report}\n\n{DISCLAIMER}"
        except Exception:
            return self._build_settlement_report_fallback(analysis, request, ai_unavailable=True)

        summary, sections = self._extract_summary_sections(markdown_report)
        return {
            "title": "SmartFX AI 结算分析报告",
            "summary": summary,
            "sections": sections,
            "markdown_report": markdown_report,
        }
