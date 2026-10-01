"""Implementação v1 do motor: importa a saída de uma rodada a partir de um CSV.

Não calcula nada: apenas lê, valida e converte as colunas do arquivo.
"""

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.engine.base import RecommendationIn
from app.models.enums import CHANNEL_BY_LABEL, RISK_BY_LABEL, RecommendationType

REQUIRED_COLUMNS = [
    "prioridade", "sku", "produto", "categoria", "curva_abc", "canal", "preco_atual",
    "preco_mercado", "menor_concorrente", "custo", "margem_atual", "margem_minima", "margem_alvo",
    "margem_liquida", "estoque", "cobertura_dias", "tendencia_mes", "var_12m", "recomendacao",
    "preco_sugerido", "variacao", "margem_resultante", "nivel_risco", "risco_score",
    "confianca_dados", "exige_aprovacao", "receita_mensal_est", "impacto_mensal_est",
    "justificativa", "motivos_revisao", "alertas_dados", "rodada_data",
]  # fmt: skip


class CsvValidationError(Exception):
    def __init__(self, errors: list[dict[str, Any]]):
        super().__init__(f"{len(errors)} erro(s) no CSV")
        self.errors = errors


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split("; ") if part.strip()]


class _RowParser:
    def __init__(self, row: dict[str, str], line: int, errors: list[dict[str, Any]]):
        self.row, self.line, self.errors = row, line, errors

    def _fail(self, field: str, message: str) -> None:
        self.errors.append({"linha": self.line, "campo": field, "erro": message})

    def text(self, field: str, required: bool = True) -> str:
        value = (self.row.get(field) or "").strip()
        if required and not value:
            self._fail(field, "obrigatório")
        return value

    def decimal(self, field: str, required: bool = True) -> Decimal | None:
        raw = (self.row.get(field) or "").strip()
        if not raw:
            if required:
                self._fail(field, "obrigatório")
            return None
        try:
            return Decimal(raw)
        except InvalidOperation:
            self._fail(field, f"número inválido: {raw!r}")
            return None

    def integer(self, field: str, required: bool = True) -> int | None:
        value = self.decimal(field, required)
        if value is None:
            return None
        if value != value.to_integral_value():
            self._fail(field, f"inteiro inválido: {value}")
            return None
        return int(value)

    def boolean(self, field: str) -> bool:
        raw = (self.row.get(field) or "").strip().lower()
        if raw in ("true", "1", "sim", "verdadeiro"):
            return True
        if raw in ("false", "0", "nao", "não", "falso", ""):
            return False
        self._fail(field, f"booleano inválido: {raw!r}")
        return False

    def mapped(self, field: str, mapping: dict[str, Any]) -> Any:
        raw = self.text(field)
        if raw and raw not in mapping:
            self._fail(field, f"valor inválido: {raw!r} (esperado: {', '.join(mapping)})")
            return None
        return mapping.get(raw)


class CsvImportEngine:
    source = "csv_import"

    def __init__(self, content: bytes | str, filename: str | None = None):
        self.filename = filename
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        self._reader_text = text

    def _rows(self) -> list[dict[str, str]]:
        reader = csv.DictReader(io.StringIO(self._reader_text))
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise CsvValidationError(
                [{"linha": 1, "campo": c, "erro": "coluna ausente"} for c in missing]
            )
        return list(reader)

    def detect_round_date(self) -> date:
        """Data da rodada, lida da coluna `rodada_data` (deve ser única no arquivo)."""
        rows = self._rows()
        if not rows:
            raise CsvValidationError([{"linha": 2, "campo": None, "erro": "arquivo sem linhas"}])
        values = {(r.get("rodada_data") or "").strip() for r in rows}
        if len(values) != 1:
            raise CsvValidationError(
                [
                    {
                        "linha": None,
                        "campo": "rodada_data",
                        "erro": "o arquivo deve ter uma única data",
                    }
                ]
            )
        raw = values.pop()
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise CsvValidationError(
                [{"linha": 2, "campo": "rodada_data", "erro": f"data inválida: {raw!r}"}]
            ) from exc

    def run(self, round_date: date) -> list[RecommendationIn]:
        rows = self._rows()
        errors: list[dict[str, Any]] = []
        items: list[RecommendationIn] = []
        seen: set[tuple[str, Any]] = set()
        recommendation_map = {r.value: r for r in RecommendationType}

        for index, row in enumerate(rows, start=2):  # linha 1 é o cabeçalho
            p = _RowParser(row, index, errors)
            before = len(errors)
            raw_date = p.text("rodada_data")
            if raw_date and raw_date != round_date.isoformat():
                p._fail("rodada_data", f"esperado {round_date.isoformat()}, veio {raw_date}")
            curve = p.text("curva_abc")
            if curve and curve not in ("A", "B", "C"):
                p._fail("curva_abc", f"valor inválido: {curve!r}")
            data = dict(
                priority=p.integer("prioridade"),
                sku=p.text("sku"),
                product_name=p.text("produto"),
                category=p.text("categoria"),
                abc_curve=curve,
                channel=p.mapped("canal", CHANNEL_BY_LABEL),
                current_price=p.decimal("preco_atual"),
                market_price=p.decimal("preco_mercado", required=False),
                lowest_valid_competitor=p.decimal("menor_concorrente", required=False),
                cost=p.decimal("custo"),
                current_margin=p.decimal("margem_atual"),
                min_margin=p.decimal("margem_minima"),
                target_margin=p.decimal("margem_alvo"),
                net_margin=p.decimal("margem_liquida", required=False),
                stock_qty=p.integer("estoque", required=False),
                coverage_days=p.decimal("cobertura_dias", required=False),
                sales_trend_month=p.decimal("tendencia_mes", required=False),
                sales_var_12m=p.decimal("var_12m", required=False),
                recommendation=p.mapped("recomendacao", recommendation_map),
                suggested_price=p.decimal("preco_sugerido"),
                variation=p.decimal("variacao"),
                resulting_margin=p.decimal("margem_resultante"),
                risk_level=p.mapped("nivel_risco", RISK_BY_LABEL),
                risk_score=p.decimal("risco_score", required=False),
                data_confidence=p.decimal("confianca_dados", required=False),
                requires_approval=p.boolean("exige_aprovacao"),
                est_monthly_revenue=p.decimal("receita_mensal_est", required=False),
                est_monthly_impact=p.decimal("impacto_mensal_est", required=False),
                justification=p.text("justificativa"),
                review_reasons=_split(row.get("motivos_revisao") or ""),
                data_alerts=_split(row.get("alertas_dados") or ""),
            )
            key = (data["sku"], data["channel"])
            if key in seen:
                p._fail("sku", f"SKU × canal duplicado: {data['sku']} / {row.get('canal')}")
            seen.add(key)
            if len(errors) == before:
                items.append(RecommendationIn(**data))

        if errors:
            raise CsvValidationError(errors)
        if not items:
            raise CsvValidationError([{"linha": 2, "campo": None, "erro": "arquivo sem linhas"}])
        return items
