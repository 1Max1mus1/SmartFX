from src.services.daily_report_service import DailyReportService


async def run_daily_report_job(session):
    return await DailyReportService.generate_today_report(session)

