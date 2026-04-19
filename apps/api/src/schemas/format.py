from fastapi import HTTPException
from pydantic import BaseModel


class Response(BaseModel):
    status_code: int
    detail: str


class ResponseFormatter(BaseModel):
    prefix: str = ""

    def ok(self, detail: str = "success") -> Response:
        return Response(status_code=200, detail=f"{self.prefix} {detail}".strip())

    def error(self, code: int, detail: str) -> Response:
        return Response(status_code=code, detail=f"{self.prefix} {detail}".strip())


def router_response_handler(response: Response) -> None:
    if response.status_code >= 300:
        raise HTTPException(status_code=response.status_code, detail=response.detail)

