from app.models import Recommendation


class StaticExplainer:
    """v1: devolve a justificativa que veio pronta na rodada (coluna `justificativa`)."""

    def explain(self, rec: Recommendation) -> str:
        return rec.justification
