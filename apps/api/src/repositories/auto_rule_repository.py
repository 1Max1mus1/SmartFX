from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert_history import AlertHistory
from src.models.auto_decision_rule import AutoDecisionRule


class AutoRuleRepository:
    @staticmethod
    async def create_rule(session: AsyncSession, rule: AutoDecisionRule) -> AutoDecisionRule:
        session.add(rule)
        await session.flush()
        await session.refresh(rule)
        return rule

    @staticmethod
    async def get_rule(session: AsyncSession, rule_id: str) -> AutoDecisionRule | None:
        result = await session.execute(select(AutoDecisionRule).where(AutoDecisionRule.id == rule_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_rules_by_user(session: AsyncSession, user_id: str) -> list[AutoDecisionRule]:
        result = await session.execute(
            select(AutoDecisionRule)
            .where(AutoDecisionRule.user_id == user_id, AutoDecisionRule.is_active.is_(True))
            .order_by(desc(AutoDecisionRule.updated_at))
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_history(session: AsyncSession, history: AlertHistory) -> AlertHistory:
        session.add(history)
        await session.flush()
        await session.refresh(history)
        return history

    @staticmethod
    async def list_history_by_user(
        session: AsyncSession,
        user_id: str,
        rule_id: str | None = None,
        limit: int = 20,
    ) -> list[AlertHistory]:
        statement = select(AlertHistory).where(AlertHistory.user_id == user_id)
        if rule_id:
            statement = statement.where(AlertHistory.rule_id == rule_id)
        statement = statement.order_by(desc(AlertHistory.created_at)).limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
