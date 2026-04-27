from __future__ import annotations

import asyncio
import json
import re
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
        last_error: Exception | None = None

        for attempt in range(3):
            try:
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
                    return self._extract_message_content(response.json())
            except Exception as exc:
                last_error = exc
                if attempt == 2:
                    break
                await asyncio.sleep(0.6 * (attempt + 1))

        assert last_error is not None
        raise last_error

    def _extract_message_content(self, payload: dict) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("AI response missing choices")

        first_choice = choices[0] if isinstance(choices[0], dict) else {}
        message = first_choice.get("message") if isinstance(first_choice, dict) else {}
        if not isinstance(message, dict):
            raise ValueError("AI response missing message")

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
                    continue
                nested_text = item.get("content")
                if isinstance(nested_text, str) and nested_text.strip():
                    chunks.append(nested_text.strip())
            if chunks:
                return "\n".join(chunks)

        raise ValueError("AI response missing textual content")

    def _extract_json_object(self, text: str) -> dict:
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
        candidate = fenced_match.group(1) if fenced_match else text
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("AI response missing JSON object")
        return json.loads(candidate[start : end + 1])

    def _finalize_student_payment_advice_markdown(self, markdown: str, fallback: str) -> str:
        if not isinstance(markdown, str) or len(markdown.strip()) < 40:
            return fallback
        if DISCLAIMER not in markdown:
            markdown = f"{markdown}\n\n{DISCLAIMER}"
        return markdown

    async def generate_student_payment_advice(self, request: dict, advice_context: dict, fallback_markdown: str) -> str:
        if self.provider == "mock" or not self.api_key:
            return fallback_markdown

        system_prompt = (
            "You are SmartFX's student tuition payment advisor. "
            "Respond in concise Simplified Chinese markdown. "
            "You must explain the recommendation clearly, but you must not promise future price moves, "
            "guaranteed savings, or certainty. Use words like 建议, 参考, 观察窗口. "
            f"You must keep this exact disclaimer at the end: {DISCLAIMER}"
        )
        user_prompt = (
            "Please rewrite the rule-based student payment advice into a user-friendly markdown answer.\n"
            "Keep the recommendation itself unchanged. Do not invent new market data.\n"
            "Prefer this structure:\n"
            "## 今日建议\n"
            "## 为什么这样判断\n"
            "## 操作建议\n"
            "## 风险提醒\n\n"
            f"User request:\n{request}\n\n"
            f"Rule-based advice context:\n{advice_context}\n\n"
            f"Fallback markdown:\n{fallback_markdown}"
        )

        try:
            markdown = await self._chat_completion(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=900,
            )
            return self._finalize_student_payment_advice_markdown(markdown, fallback_markdown)
        except Exception:
            return fallback_markdown

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

    def _build_settlement_window_fallback(self, analysis: dict, request: dict, *, ai_unavailable: bool) -> dict:
        percentile_30d = analysis["current_percentile_30d"]
        if request["optimization_goal"] == "maximize_income":
            if percentile_30d >= 80:
                days = 2
            elif percentile_30d >= 60:
                days = 4
            elif percentile_30d <= 25:
                days = 9
            else:
                days = 6
        else:
            if percentile_30d <= 20:
                days = 1
            elif percentile_30d <= 40:
                days = 3
            elif percentile_30d >= 75:
                days = 7
            else:
                days = 5

        source_label = "基础规则" if ai_unavailable else "默认模型"
        reason = (
            f"{source_label}判断当前 30 天分位为 {percentile_30d:.2f}% ，"
            f"结合 {analysis['zone_label']} 区间位置与 {request['optimization_goal']} 目标，"
            f"建议先观察 {days} 天，再结合到账节奏决定是否执行。"
        )
        return {
            "recommended_window_days": days,
            "recommended_window_reason": reason,
        }

    def _build_settlement_report_fallback(self, analysis: dict, request: dict, *, ai_unavailable: bool) -> dict:
        business_impact = self._settlement_business_impact(analysis, request)
        scenario = self._infer_settlement_scenario(request)
        title = "SmartFX AI 结算分析报告"
        summary = (
            f"本次结算场景为{scenario['scenario_name']}，即 {request['amount']} {request['source_currency']} "
            f"兑换为 {request['target_currency']}。当前参考汇率为 {analysis['current_rate']:.4f}，"
            f"立即结算的参考价值约为 {analysis['immediate_value']:.2f}。若等待更优窗口，"
            f"对{business_impact['impact_direction']}的参考改善约为 {business_impact['estimated_delta']:.2f}，"
            f"约占本次结算金额的 {business_impact['delta_ratio_pct']:.2f}%，应重点关注"
            f"{scenario['focus_metric']}。"
        )
        sections = [
            (
                f"商业影响：当前立即结算参考价值约为 {business_impact['immediate_value']:.2f}，"
                f"更优窗口下可能达到 {business_impact['projected_best_case_value']:.2f}，"
                f"两者差额约为 {business_impact['estimated_delta']:.2f}，可视为本次结算对"
                f"{scenario['focus_metric']}的波动区间。"
            ),
            (
                f"执行建议：当前区间位置为 {analysis['zone_label']}，建议结合 "
                f"{analysis['recommended_window_days']} 天观察窗口、到账时间和资金安排来执行。"
            ),
            f"窗口理由：{analysis['recommended_window_reason']}",
            (
                f"经营提示：建议把 {business_impact['estimated_delta']:.2f} {request['target_currency']} "
                f"视为经营敏感差额，{scenario['management_action']}。"
            ),
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

        summary = next((line for line in content_lines if line not in {"摘要", "关键结论"}), "暂无可用摘要。")
        sections = [line for line in content_lines if line not in {"摘要", "关键结论", summary}]
        return summary, sections[:5]

    def _finalize_settlement_report(self, markdown_report: str, analysis: dict, request: dict) -> dict:
        if not isinstance(markdown_report, str) or len(markdown_report.strip()) < 40:
            return self._build_settlement_report_fallback(analysis, request, ai_unavailable=True)

        if DISCLAIMER not in markdown_report:
            markdown_report = f"{markdown_report}\n\n{DISCLAIMER}"

        summary, sections = self._extract_summary_sections(markdown_report)
        if not summary.strip() or len(sections) < 2:
            return self._build_settlement_report_fallback(analysis, request, ai_unavailable=True)

        return {
            "title": "SmartFX AI 结算分析报告",
            "summary": summary,
            "sections": sections,
            "markdown_report": markdown_report,
        }

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

    async def recommend_settlement_window(self, analysis: dict, request: dict, market_context: dict) -> dict:
        fallback = self._build_settlement_window_fallback(analysis, request, ai_unavailable=self.provider != "mock")
        if self.provider == "mock" or not self.api_key:
            return fallback

        prompt = (
            "请你为这次结算分析给出一个建议观察窗口，只返回 JSON，不要输出 Markdown。\n"
            "JSON 格式必须是："
            '{"recommended_window_days": 3, "recommended_window_reason": "一句到两句中文说明"}。\n'
            "天数必须是 1 到 14 之间的整数。说明要结合当前汇率位置、近 30/90 天分位、近 7 天波动、到账日和业务目标。"
            "不要使用投资承诺措辞。\n"
            f"结算请求：{request}\n"
            f"分析结果：{analysis}\n"
            f"市场上下文：{market_context}"
        )

        try:
            content = await self._chat_completion(
                [
                    {
                        "role": "system",
                        "content": "你是 SmartFX 的结算窗口建议助手，只输出合法 JSON。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=240,
            )
            payload = self._extract_json_object(content)
            days = int(payload["recommended_window_days"])
            reason = str(payload["recommended_window_reason"]).strip()
            if not reason:
                raise ValueError("empty recommended_window_reason")
            return {
                "recommended_window_days": min(14, max(1, days)),
                "recommended_window_reason": reason,
            }
        except Exception:
            return self._build_settlement_window_fallback(analysis, request, ai_unavailable=True)

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
            "报告里请明确引用建议观察窗口天数和窗口理由。"
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
                            "你的重点是把汇率变化对业务利润、成本、回款折算、报价和预算的影响说明清楚，"
                            "并给出可执行的结算建议。请多使用金额、差额、占比来支撑结论。"
                            "如果是出口收汇，就多讲回款折算和利润释放；如果是进口付汇，就多讲采购成本和预算消耗。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
            )
        except Exception:
            return self._build_settlement_report_fallback(analysis, request, ai_unavailable=True)

        return self._finalize_settlement_report(markdown_report, analysis, request)
