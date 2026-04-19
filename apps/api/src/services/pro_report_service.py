from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.kimi_client import KimiClient
from src.models.report_job import ReportJob
from src.models.user import User
from src.repositories.report_job_repository import ReportJobRepository
from src.schemas.format import ResponseFormatter
from src.schemas.settlement import ReportJobCreatePayload, ReportJobStatusPayload, SettlementRequest
from src.services.auth_service import DEMO_USER_ID
from src.services.db import SessionLocal
from src.services.settlement_service import SettlementService

RESPONSE = ResponseFormatter(prefix="[ProReportService]")
DEMO_REPORT_JOBS: dict[str, dict] = {}


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ProReportService:
    @staticmethod
    async def create_report_job(session: AsyncSession, user: User, request: SettlementRequest) -> tuple[dict, object]:
        if user.id == DEMO_USER_ID:
            job_id = str(uuid4())
            created_at = _utcnow()
            DEMO_REPORT_JOBS[job_id] = {
                "job_id": job_id,
                "user_id": user.id,
                "job_status": "pending",
                "input_payload": request.model_dump(mode="json"),
                "result": None,
                "error_message": None,
                "created_at": created_at,
                "updated_at": created_at,
            }
            asyncio.get_running_loop().create_task(ProReportService._run_demo_report_job(job_id))
            payload = ReportJobCreatePayload(job_id=job_id, job_status="pending", created_at=created_at)
            return payload.model_dump(mode="json"), RESPONSE.ok("demo report job created")

        job = ReportJob(
            user_id=user.id,
            job_type="settlement_report",
            job_status="pending",
            input_payload=json.dumps(request.model_dump(mode="json"), ensure_ascii=False),
        )
        job = await ReportJobRepository.create(session, job)
        await session.commit()

        asyncio.get_running_loop().create_task(ProReportService._run_report_job(job.id))
        payload = ReportJobCreatePayload(job_id=job.id, job_status=job.job_status, created_at=job.created_at)
        return payload.model_dump(mode="json"), RESPONSE.ok("report job created")

    @staticmethod
    async def get_report_job_status(session: AsyncSession, user: User, job_id: str) -> tuple[dict, object]:
        if user.id == DEMO_USER_ID:
            job = DEMO_REPORT_JOBS.get(job_id)
            if not job or job["user_id"] != user.id:
                return {}, RESPONSE.error(404, "report job not found")

            payload = ReportJobStatusPayload(
                job_id=job["job_id"],
                job_status=job["job_status"],
                result=job["result"],
                error_message=job["error_message"],
                updated_at=job["updated_at"],
            )
            return payload.model_dump(mode="json"), RESPONSE.ok("demo report job status ready")

        job = await ReportJobRepository.get_by_id(session, job_id)
        if not job or job.user_id != user.id:
            return {}, RESPONSE.error(404, "report job not found")

        payload = ReportJobStatusPayload(
            job_id=job.id,
            job_status=job.job_status,
            result=json.loads(job.result_payload) if job.result_payload else None,
            error_message=job.error_message,
            updated_at=job.updated_at,
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("report job status ready")

    @staticmethod
    async def _run_report_job(job_id: str) -> None:
        async with SessionLocal() as session:
            job = await ReportJobRepository.get_by_id(session, job_id)
            if not job:
                return

            try:
                job.job_status = "running"
                await session.commit()

                request_payload = SettlementRequest.model_validate(json.loads(job.input_payload))
                analysis_payload, response = await SettlementService.analyze(request_payload)
                if response.status_code >= 300:
                    raise RuntimeError(response.detail)

                ai_report = await KimiClient().generate_settlement_report(
                    analysis_payload,
                    request_payload.model_dump(mode="json"),
                )
                result_payload = {
                    **ai_report,
                    "analysis": analysis_payload,
                }
                job.result_payload = json.dumps(result_payload, ensure_ascii=False)
                job.job_status = "done"
                job.error_message = None
                await session.commit()
            except Exception as exc:
                job.job_status = "failed"
                job.error_message = str(exc)
                await session.commit()

    @staticmethod
    async def _run_demo_report_job(job_id: str) -> None:
        job = DEMO_REPORT_JOBS.get(job_id)
        if not job:
            return

        try:
            job["job_status"] = "running"
            job["updated_at"] = _utcnow()

            request_payload = SettlementRequest.model_validate(job["input_payload"])
            analysis_payload, response = await SettlementService.analyze(request_payload)
            if response.status_code >= 300:
                raise RuntimeError(response.detail)

            ai_report = await KimiClient().generate_settlement_report(
                analysis_payload,
                request_payload.model_dump(mode="json"),
            )
            job["result"] = {
                **ai_report,
                "analysis": analysis_payload,
            }
            job["job_status"] = "done"
            job["error_message"] = None
            job["updated_at"] = _utcnow()
        except Exception as exc:
            job["job_status"] = "failed"
            job["error_message"] = str(exc)
            job["updated_at"] = _utcnow()
