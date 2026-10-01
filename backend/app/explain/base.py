"""Ponto de extensão da IA generativa (justificativa em linguagem natural)."""

from typing import Protocol

from app.models import Recommendation


class Explainer(Protocol):
    def explain(self, rec: Recommendation) -> str: ...
