"""Sincronização (simulada) com o ERP.

O "ERP" é a planilha `seed/base_popular_pet.xlsx` (ou um arquivo exportado do ERP enviado pelo
usuário). Cada sincronização lê as abas Produtos, Precos_Atuais, Custos_Margens, Estoque e
Historico_Precos, atualiza o cadastro, o estado por canal e o estoque, e registra cada alteração de
preço em `price_history`. Toda execução fica gravada em `erp_sync_runs`, com sucesso ou erro.
"""

import io
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    ErpSyncRun,
    PriceChangeType,
    PriceHistory,
    Product,
    ProductChannelState,
    StockSnapshot,
    SyncStatus,
    SyncTrigger,
)
from app.models.enums import CHANNEL_BY_LABEL, Channel

log = logging.getLogger(__name__)

ERP_SOURCE_LABEL = "ERP Popular Pet (simulado)"
HISTORY_SOURCE = "ERP_HISTORICO"
SYNC_SOURCE = "ERP_SYNC"
# A aba Historico_Precos não tem canal; o preço registrado é o da loja física (DECISOES D29).
HISTORY_CHANNEL = Channel.LOJA_FISICA

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "Produtos": ["SKU", "Produto", "Categoria", "Marca", "Curva ABC", "Status"],
    "Precos_Atuais": ["SKU", "Canal", "Preço atual", "Data referência"],
    "Custos_Margens": [
        "SKU", "Canal", "Custo reposição", "Impostos estimados", "Frete rateado", "Taxa canal",
        "Margem mínima", "Margem alvo",
    ],
    "Estoque": [
        "SKU", "Estoque atual", "Cobertura dias", "Pedido compra aberto", "Previsão recebimento",
        "Local",
    ],
}  # fmt: skip
HISTORY_COLUMNS = ["SKU", "Data", "Preço", "Motivo", "Origem"]
CENT = Decimal("0.01")


class ErpFileError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def default_source_file() -> Path:
    return Path(settings.erp_source_file or Path(settings.seed_dir) / "base_popular_pet.xlsx")


# --- Leitura e validação ---------------------------------------------------------------------


@dataclass
class ChannelRow:
    sku: str
    channel: Channel
    reference_date: date
    price: Decimal
    replacement_cost: Decimal
    taxes: Decimal
    freight: Decimal
    channel_fee: Decimal
    min_margin: Decimal
    target_margin: Decimal


@dataclass
class ErpData:
    products: list[dict] = field(default_factory=list)
    channels: list[ChannelRow] = field(default_factory=list)
    stock: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)


def _blank(value: object) -> bool:
    return (
        value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == ""
    )


def _date(value: object, where: str, errors: list[str]) -> date | None:
    if _blank(value):
        return None
    if isinstance(value, datetime | pd.Timestamp):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%d/%m/%Y").date()
    except ValueError:
        errors.append(f"{where}: data inválida {value!r} (esperado dd/mm/aaaa)")
        return None


def _dec(value: object, where: str, errors: list[str], places: str = "0.01") -> Decimal:
    try:
        if _blank(value):
            raise InvalidOperation
        return Decimal(str(value)).quantize(Decimal(places))
    except (InvalidOperation, ValueError):
        errors.append(f"{where}: número inválido {value!r}")
        return Decimal(0)


def read_workbook(content: bytes | Path) -> ErpData:
    """Lê e valida a planilha do ERP. Levanta ErpFileError com a lista de problemas."""
    try:
        book = pd.ExcelFile(io.BytesIO(content) if isinstance(content, bytes) else content)
    except Exception as exc:  # arquivo corrompido, formato errado…
        raise ErpFileError(["não foi possível ler o arquivo como planilha Excel (.xlsx)"]) from exc

    errors: list[str] = []
    sheets: dict[str, pd.DataFrame] = {}
    for sheet, columns in {**REQUIRED_COLUMNS, "Historico_Precos": HISTORY_COLUMNS}.items():
        if sheet not in book.sheet_names:
            if sheet in REQUIRED_COLUMNS:
                errors.append(f"aba ausente: {sheet}")
            continue
        df = pd.read_excel(book, sheet, header=2, dtype=object)
        missing = [c for c in columns if c not in df.columns]
        if missing:
            errors.append(f"aba {sheet}: coluna(s) ausente(s): {', '.join(missing)}")
            continue
        sheets[sheet] = df.dropna(how="all")
    if errors:
        raise ErpFileError(errors)

    data = ErpData()
    for i, r in sheets["Produtos"].iterrows():
        where = f"Produtos, linha {i + 4}"
        curve = str(r["Curva ABC"]).strip()
        if curve not in ("A", "B", "C"):
            errors.append(f"{where}: curva ABC inválida {curve!r}")
        data.products.append(
            {
                "sku": str(r["SKU"]).strip(),
                "name": str(r["Produto"]).strip(),
                "category": str(r["Categoria"]).strip(),
                "brand": str(r["Marca"]).strip(),
                "abc_curve": curve,
                "status": str(r["Status"]).strip(),
            }
        )
    skus = {p["sku"] for p in data.products}

    costs = {
        (str(r["SKU"]).strip(), str(r["Canal"]).strip()): (i, r)
        for i, r in sheets["Custos_Margens"].iterrows()
    }
    for i, r in sheets["Precos_Atuais"].iterrows():
        where = f"Precos_Atuais, linha {i + 4}"
        sku, label = str(r["SKU"]).strip(), str(r["Canal"]).strip()
        channel = CHANNEL_BY_LABEL.get(label)
        if channel is None:
            errors.append(f"{where}: canal inválido {label!r}")
            continue
        if sku not in skus:
            errors.append(f"{where}: SKU {sku} não está na aba Produtos")
            continue
        if (sku, label) not in costs:
            errors.append(f"{where}: {sku} / {label} sem linha em Custos_Margens")
            continue
        ref = _date(r["Data referência"], where, errors)
        if ref is None:
            errors.append(f"{where}: data de referência obrigatória")
            continue
        ci, c = costs[(sku, label)]
        cwhere = f"Custos_Margens, linha {ci + 4}"
        data.channels.append(
            ChannelRow(
                sku=sku,
                channel=channel,
                reference_date=ref,
                price=_dec(r["Preço atual"], where, errors),
                replacement_cost=_dec(c["Custo reposição"], cwhere, errors),
                taxes=_dec(c["Impostos estimados"], cwhere, errors),
                freight=_dec(c["Frete rateado"], cwhere, errors),
                channel_fee=_dec(c["Taxa canal"], cwhere, errors, "0.0001"),
                min_margin=_dec(c["Margem mínima"], cwhere, errors, "0.0001"),
                target_margin=_dec(c["Margem alvo"], cwhere, errors, "0.0001"),
            )
        )

    for i, r in sheets["Estoque"].iterrows():
        where = f"Estoque, linha {i + 4}"
        sku = str(r["SKU"]).strip()
        if sku not in skus:
            errors.append(f"{where}: SKU {sku} não está na aba Produtos")
            continue
        data.stock.append(
            {
                "sku": sku,
                "quantity": int(_dec(r["Estoque atual"], where, errors, "1")),
                "coverage_days": _dec(r["Cobertura dias"], where, errors, "0.1"),
                "open_po_quantity": int(_dec(r["Pedido compra aberto"], where, errors, "1")),
                "expected_receipt": _date(r["Previsão recebimento"], where, errors),
                "location": None if _blank(r["Local"]) else str(r["Local"]).strip(),
            }
        )

    for i, r in sheets.get("Historico_Precos", pd.DataFrame()).iterrows():
        where = f"Historico_Precos, linha {i + 4}"
        sku = str(r["SKU"]).strip()
        if sku not in skus:
            errors.append(f"{where}: SKU {sku} não está na aba Produtos")
            continue
        when = _date(r["Data"], where, errors)
        if when is None:
            continue
        data.history.append(
            {
                "sku": sku,
                "date": when,
                "price": _dec(r["Preço"], where, errors),
                "reason": None if _blank(r["Motivo"]) else str(r["Motivo"]).strip(),
                "origin": None if _blank(r["Origem"]) else str(r["Origem"]).strip(),
            }
        )

    if errors:
        raise ErpFileError(
            errors[:50] + ([f"… e mais {len(errors) - 50}"] if len(errors) > 50 else [])
        )
    return data


# --- Aplicação no banco ----------------------------------------------------------------------


def _change(old: Decimal | None, new: Decimal) -> tuple[PriceChangeType, Decimal | None]:
    if old is None:
        return PriceChangeType.INICIAL, None
    kind = PriceChangeType.AUMENTO if new > old else PriceChangeType.REDUCAO
    return kind, (new / old - 1).quantize(Decimal("0.0001")) if old else None


def _apply(session: Session, data: ErpData, run: ErpSyncRun) -> None:
    # 1. Cadastro de produtos
    existing = {p.sku: p for p in session.scalars(select(Product))}
    for row in data.products:
        product = existing.get(row["sku"])
        if product is None:
            session.add(Product(**row))
            run.products_new += 1
        elif any(getattr(product, k) != v for k, v in row.items()):
            for k, v in row.items():
                setattr(product, k, v)
            run.products_updated += 1
    run.products_total = len(data.products)
    session.flush()

    # Linha do tempo atual de preços por SKU × canal
    timeline: dict[tuple[str, Channel], list[PriceHistory]] = {}
    for event in session.scalars(
        select(PriceHistory).order_by(PriceHistory.effective_date, PriceHistory.created_at)
    ):
        timeline.setdefault((event.sku, event.channel), []).append(event)

    def add_event(sku: str, channel: Channel, when: date, price: Decimal, **extra) -> PriceHistory:
        events = timeline.setdefault((sku, channel), [])
        previous = [e for e in events if e.effective_date <= when]
        old = previous[-1].new_price if previous else None
        kind, variation = _change(old, price)
        event = PriceHistory(
            sku=sku,
            channel=channel,
            effective_date=when,
            old_price=old,
            new_price=price,
            variation=variation,
            change_type=kind,
            sync_run_id=run.id,
            **extra,
        )
        session.add(event)
        events.append(event)
        events.sort(key=lambda e: e.effective_date)
        return event

    # 2. Histórico de preços informado pelo ERP (só registros ainda não importados)
    known = {
        (e.sku, e.effective_date, e.new_price)
        for events in timeline.values()
        for e in events
        if e.source == HISTORY_SOURCE
    }
    for row in sorted(data.history, key=lambda r: (r["sku"], r["date"])):
        if (row["sku"], row["date"], row["price"]) in known:
            continue
        events = timeline.get((row["sku"], HISTORY_CHANNEL), [])
        previous = [e for e in events if e.effective_date <= row["date"]]
        if previous and previous[-1].new_price == row["price"]:
            continue  # revisão sem mudança de preço
        add_event(
            row["sku"],
            HISTORY_CHANNEL,
            row["date"],
            row["price"],
            source=HISTORY_SOURCE,
            reason=row["reason"],
            origin=row["origin"],
        )
        run.history_imported += 1

    # 3. Preço e custos vigentes por canal
    for row in data.channels:
        events = timeline.get((row.sku, row.channel), [])
        last = events[-1].new_price if events else None
        if last != row.price:
            event = add_event(
                row.sku,
                row.channel,
                row.reference_date,
                row.price,
                source=SYNC_SOURCE,
                reason="Preço vigente no ERP",
                origin="ERP",
            )
            if event.change_type != PriceChangeType.INICIAL:
                run.prices_changed += 1
        values = {
            "current_price": row.price,
            "replacement_cost": row.replacement_cost,
            "taxes": row.taxes,
            "freight": row.freight,
            "channel_fee": row.channel_fee,
            "min_margin": row.min_margin,
            "target_margin": row.target_margin,
        }
        session.execute(
            insert(ProductChannelState)
            .values(sku=row.sku, channel=row.channel, reference_date=row.reference_date, **values)
            .on_conflict_do_update(index_elements=["sku", "channel", "reference_date"], set_=values)
        )

    # 4. Estoque (a aba não tem data: usa a data de referência dos preços — DECISOES D06)
    reference = max((r.reference_date for r in data.channels), default=date.today())
    run.reference_date = reference
    for row in data.stock:
        values = {k: v for k, v in row.items() if k != "sku"}
        session.execute(
            insert(StockSnapshot)
            .values(sku=row["sku"], reference_date=reference, **values)
            .on_conflict_do_update(index_elements=["sku", "reference_date"], set_=values)
        )
        run.stock_updated += 1


def _summary(run: ErpSyncRun) -> str:
    parts = [f"{run.products_total} produtos lidos"]
    if run.products_new:
        parts.append(f"{run.products_new} novos")
    if run.products_updated:
        parts.append(f"{run.products_updated} com cadastro atualizado")
    parts.append(
        f"{run.prices_changed} preço(s) alterado(s)"
        if run.prices_changed
        else "nenhum preço alterado"
    )
    if run.history_imported:
        parts.append(f"{run.history_imported} registro(s) de histórico importado(s)")
    return " · ".join(parts)


def run_sync(
    session: Session,
    *,
    trigger: SyncTrigger,
    content: bytes | Path | None = None,
    source: str | None = None,
    user_id: uuid.UUID | None = None,
) -> ErpSyncRun:
    """Executa uma sincronização completa e devolve o registro da execução (sempre gravado)."""
    content = content if content is not None else default_source_file()
    if source is None:
        source = f"{ERP_SOURCE_LABEL} · {content.name}" if isinstance(content, Path) else "Arquivo"
    run = ErpSyncRun(
        trigger=trigger,
        source=source,
        status=SyncStatus.EM_ANDAMENTO,
        triggered_by=user_id,
        started_at=datetime.now(UTC),
        products_total=0,
        products_new=0,
        products_updated=0,
        prices_changed=0,
        history_imported=0,
        stock_updated=0,
    )
    session.add(run)
    session.commit()
    run_id = run.id

    try:
        _apply(session, read_workbook(content), run)
        run.status = SyncStatus.SUCESSO
        run.message = _summary(run)
        run.finished_at = datetime.now(UTC)
        session.commit()
        return run
    except Exception as exc:
        session.rollback()
        if isinstance(exc, ErpFileError):
            message = "Arquivo do ERP inválido: " + "; ".join(exc.errors)
        else:
            log.exception("Falha na sincronização com o ERP")
            message = f"Falha inesperada na sincronização: {exc.__class__.__name__}"
        failed = session.get(ErpSyncRun, run_id)
        failed.status = SyncStatus.ERRO
        failed.message = message
        failed.finished_at = datetime.now(UTC)
        session.commit()
        return failed


def has_any_sync(session: Session) -> bool:
    return bool(session.scalar(select(func.count()).select_from(ErpSyncRun)))
