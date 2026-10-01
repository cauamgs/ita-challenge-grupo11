"""Erros de domínio. A camada `api/` converte em respostas HTTP com mensagem em português."""

from typing import Any


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class ValidationFailed(DomainError):
    status_code = 422

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.errors = errors or []
