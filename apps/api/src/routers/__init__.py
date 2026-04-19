from fastapi import APIRouter

from src.routers import ai_chat, auth, auto_rules, health, pro_backtest, pro_report, pro_settlement, rates, records, report

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(ai_chat.router, prefix="/ai", tags=["ai"])
router.include_router(auto_rules.router, prefix="/pro", tags=["pro"])
router.include_router(pro_backtest.router, prefix="/pro", tags=["pro"])
router.include_router(pro_settlement.router, prefix="/pro", tags=["pro"])
router.include_router(pro_report.router, prefix="/pro", tags=["pro"])
router.include_router(rates.router, prefix="/rates", tags=["rates"])
router.include_router(records.router, prefix="/records", tags=["records"])
router.include_router(report.router, prefix="/report", tags=["report"])
