from fastapi import APIRouter, Depends

from src.models.user import User
from src.schemas.format import router_response_handler
from src.schemas.student_payment import StudentPaymentAdviceRequest
from src.services.auth_service import get_current_user
from src.services.student_payment_advice_service import StudentPaymentAdviceService

router = APIRouter()


@router.post("/student-payment-advice")
async def student_payment_advice(
    request: StudentPaymentAdviceRequest,
    user: User = Depends(get_current_user),
):
    _ = user
    payload, response = await StudentPaymentAdviceService.analyze(request)
    router_response_handler(response)
    return payload
