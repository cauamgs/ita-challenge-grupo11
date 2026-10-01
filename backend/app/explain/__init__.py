from app.explain.base import Explainer
from app.explain.static import StaticExplainer

__all__ = ["Explainer", "StaticExplainer", "get_explainer"]


def get_explainer() -> Explainer:
    """v1: justificativa pronta do CSV. v2: trocar por uma implementação com LLM."""
    return StaticExplainer()
