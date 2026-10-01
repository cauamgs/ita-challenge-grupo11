from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.errors import DomainError, ValidationFailed

HTTP_MESSAGES = {
    404: "Recurso não encontrado.",
    405: "Método não permitido.",
    500: "Erro interno do servidor.",
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if not isinstance(detail, str) or detail.isascii():
            detail = HTTP_MESSAGES.get(exc.status_code, detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
        body: dict = {"detail": exc.message}
        if isinstance(exc, ValidationFailed) and exc.errors:
            body["errors"] = exc.errors
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"campo": ".".join(str(p) for p in e["loc"][1:]), "erro": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422, content={"detail": "Parâmetros inválidos.", "errors": errors}
        )
