from pathlib import Path
import asyncio
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.jobs.daily_report_job import run_daily_report_job
from src.services.db import SessionLocal, close_database, init_database


async def main() -> None:
    await init_database()
    async with SessionLocal() as session:
        payload, response = await run_daily_report_job(session)
        print(response.detail)
        print(payload["report_date"])
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())

