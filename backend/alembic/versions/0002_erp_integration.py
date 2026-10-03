"""Integração simulada com o ERP: sincronizações, agenda e histórico de preços

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENUMS = {
    "sync_trigger_t": ("INICIAL", "MANUAL", "AGENDADO", "ARQUIVO"),
    "sync_status_t": ("EM_ANDAMENTO", "SUCESSO", "ERRO"),
    "sync_frequency_t": ("DIARIA", "SEMANAL", "MENSAL"),
    "price_change_t": ("INICIAL", "AUMENTO", "REDUCAO"),
}


def enum(name: str) -> pg.ENUM:
    values = ENUMS.get(name) or ("LOJA_FISICA", "ECOMMERCE", "MARKETPLACE")
    return pg.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUMS.items():
        pg.ENUM(*values, name=name).create(bind, checkfirst=True)

    op.create_table(
        "erp_sync_runs",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("trigger", enum("sync_trigger_t"), nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("status", enum("sync_status_t"), nullable=False),
        sa.Column("triggered_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("reference_date", sa.Date),
        sa.Column("products_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("products_new", sa.Integer, nullable=False, server_default="0"),
        sa.Column("products_updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("prices_changed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("history_imported", sa.Integer, nullable=False, server_default="0"),
        sa.Column("stock_updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("message", sa.Text),
    )

    op.create_table(
        "erp_sync_schedule",
        sa.Column("id", sa.SmallInteger, primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("frequency", enum("sync_frequency_t"), nullable=False),
        sa.Column("weekday", sa.SmallInteger),
        sa.Column("day_of_month", sa.SmallInteger),
        sa.Column("time_of_day", sa.Time, nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("id = 1", name="ck_erp_sync_schedule_single_row"),
        sa.CheckConstraint("weekday between 0 and 6", name="ck_erp_sync_schedule_weekday"),
        sa.CheckConstraint("day_of_month between 1 and 28", name="ck_erp_sync_schedule_day"),
    )

    op.create_table(
        "price_history",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("sku", sa.Text, sa.ForeignKey("products.sku"), nullable=False),
        sa.Column("channel", enum("channel_t"), nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("old_price", sa.Numeric(12, 2)),
        sa.Column("new_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("variation", sa.Numeric(8, 4)),
        sa.Column("change_type", enum("price_change_t"), nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("origin", sa.Text),
        sa.Column("sync_run_id", pg.UUID(as_uuid=True), sa.ForeignKey("erp_sync_runs.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_price_history_sku_date", "price_history", ["sku", "effective_date"])
    op.create_index("ix_price_history_date", "price_history", ["effective_date"])


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("erp_sync_schedule")
    op.drop_table("erp_sync_runs")
    bind = op.get_bind()
    for name in ENUMS:
        pg.ENUM(name=name).drop(bind, checkfirst=True)
