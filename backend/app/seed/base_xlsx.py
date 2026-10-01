"""Carga da base da empresa (seed/base_popular_pet.xlsx): Produtos, Precos_Atuais, Custos_Margens,
Estoque. Cada aba tem 2 linhas de título antes do cabeçalho (header=2); datas em dd/mm/aaaa."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.enums import CHANNEL_BY_LABEL
from app.repositories import products as products_repo


def _date(value: object) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)) or value is pd.NaT:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    return datetime.strptime(text, "%d/%m/%Y").date() if text else None


def _dec(value: object, places: str = "0.01") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places))


def seed_base(session: Session, xlsx_path: Path) -> dict[str, int]:
    book = pd.ExcelFile(xlsx_path)
    products = pd.read_excel(book, "Produtos", header=2, dtype={"SKU": str})
    prices = pd.read_excel(book, "Precos_Atuais", header=2, dtype={"Data referência": str})
    costs = pd.read_excel(book, "Custos_Margens", header=2)
    stock = pd.read_excel(book, "Estoque", header=2, dtype={"Previsão recebimento": str})

    products_repo.insert_products(
        session,
        [
            {
                "sku": r["SKU"],
                "name": r["Produto"],
                "category": r["Categoria"],
                "brand": r["Marca"],
                "abc_curve": r["Curva ABC"],
                "status": r["Status"],
            }
            for _, r in products.iterrows()
        ],
    )

    merged = prices.merge(costs, on=["SKU", "Canal"], how="inner", validate="one_to_one")
    states = []
    for _, r in merged.iterrows():
        states.append(
            {
                "sku": r["SKU"],
                "channel": CHANNEL_BY_LABEL[r["Canal"]],
                "reference_date": _date(r["Data referência"]),
                "current_price": _dec(r["Preço atual"]),
                "replacement_cost": _dec(r["Custo reposição"]),
                "taxes": _dec(r["Impostos estimados"]),
                "freight": _dec(r["Frete rateado"]),
                "channel_fee": _dec(r["Taxa canal"], "0.0001"),
                "min_margin": _dec(r["Margem mínima"], "0.0001"),
                "target_margin": _dec(r["Margem alvo"], "0.0001"),
            }
        )
    products_repo.insert_channel_states(session, states)

    # A aba Estoque não tem data; usamos a data de referência dos preços (ver docs/DECISOES.md).
    stock_date = max(s["reference_date"] for s in states)
    products_repo.insert_stock(
        session,
        [
            {
                "sku": r["SKU"],
                "reference_date": stock_date,
                "quantity": int(r["Estoque atual"]),
                "coverage_days": _dec(r["Cobertura dias"], "0.1"),
                "open_po_quantity": int(r["Pedido compra aberto"]),
                "expected_receipt": _date(r["Previsão recebimento"]),
                "location": r["Local"],
            }
            for _, r in stock.iterrows()
        ],
    )
    session.flush()
    return {"products": len(products), "channel_states": len(states), "stock": len(stock)}
