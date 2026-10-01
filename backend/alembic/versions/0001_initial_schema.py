"""Schema inicial (DATA_MODEL.md)

Revision ID: 0001
Revises:
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENUMS = {
    "channel_t": ("LOJA_FISICA", "ECOMMERCE", "MARKETPLACE"),
    "recommendation_t": ("SUBIR", "BAIXAR", "MANTER", "REVISAR"),
    "risk_t": ("BAIXO", "MEDIO", "ALTO"),
    "decision_t": ("APROVAR", "EDITAR", "REJEITAR", "ADIAR"),
    "user_role_t": ("ANALISTA", "GESTOR"),
}


def enum(name: str) -> pg.ENUM:
    return pg.ENUM(*ENUMS[name], name=name, create_type=False)


def uuid_pk() -> sa.Column:
    return sa.Column(
        "id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )


def created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUMS.items():
        pg.ENUM(*values, name=name).create(bind, checkfirst=True)

    op.create_table(
        "users",
        uuid_pk(),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("role", enum("user_role_t"), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        created_at(),
    )

    op.create_table(
        "products",
        sa.Column("sku", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("brand", sa.Text, nullable=False),
        sa.Column("abc_curve", sa.String(1), nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("is_strategic", sa.Boolean, nullable=False, server_default=sa.text("false")),
        created_at(),
        sa.CheckConstraint("abc_curve in ('A','B','C')", name="ck_products_abc_curve"),
    )

    op.create_table(
        "product_channel_state",
        uuid_pk(),
        sa.Column("sku", sa.Text, sa.ForeignKey("products.sku"), nullable=False),
        sa.Column("channel", enum("channel_t"), nullable=False),
        sa.Column("reference_date", sa.Date, nullable=False),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("replacement_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("taxes", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("freight", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("channel_fee", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("min_margin", sa.Numeric(8, 4), nullable=False),
        sa.Column("target_margin", sa.Numeric(8, 4), nullable=False),
        sa.UniqueConstraint("sku", "channel", "reference_date"),
    )

    op.create_table(
        "stock_snapshot",
        uuid_pk(),
        sa.Column("sku", sa.Text, sa.ForeignKey("products.sku"), nullable=False),
        sa.Column("reference_date", sa.Date, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("coverage_days", sa.Numeric(8, 1)),
        sa.Column("open_po_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expected_receipt", sa.Date),
        sa.Column("location", sa.Text),
        sa.UniqueConstraint("sku", "reference_date"),
    )

    op.create_table(
        "rounds",
        uuid_pk(),
        sa.Column("round_date", sa.Date, nullable=False, unique=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("source_file", sa.Text),
        sa.Column("imported_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        created_at(),
    )

    op.create_table(
        "recommendations",
        uuid_pk(),
        sa.Column(
            "round_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("rounds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("sku", sa.Text, sa.ForeignKey("products.sku"), nullable=False),
        sa.Column("channel", enum("channel_t"), nullable=False),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("market_price", sa.Numeric(12, 2)),
        sa.Column("lowest_valid_competitor", sa.Numeric(12, 2)),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("current_margin", sa.Numeric(8, 4), nullable=False),
        sa.Column("min_margin", sa.Numeric(8, 4), nullable=False),
        sa.Column("target_margin", sa.Numeric(8, 4), nullable=False),
        sa.Column("net_margin", sa.Numeric(8, 4)),
        sa.Column("stock_qty", sa.Integer),
        sa.Column("coverage_days", sa.Numeric(8, 1)),
        sa.Column("sales_trend_month", sa.Numeric(8, 4)),
        sa.Column("sales_var_12m", sa.Numeric(8, 4)),
        sa.Column("recommendation", enum("recommendation_t"), nullable=False),
        sa.Column("suggested_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("variation", sa.Numeric(8, 4), nullable=False),
        sa.Column("resulting_margin", sa.Numeric(8, 4), nullable=False),
        sa.Column("risk_level", enum("risk_t"), nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 1)),
        sa.Column("data_confidence", sa.Numeric(5, 3)),
        sa.Column("requires_approval", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("est_monthly_revenue", sa.Numeric(14, 2)),
        sa.Column("est_monthly_impact", sa.Numeric(14, 2)),
        sa.Column("justification", sa.Text, nullable=False),
        sa.Column("review_reasons", pg.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("data_alerts", pg.ARRAY(sa.Text), nullable=False, server_default="{}"),
        created_at(),
        sa.UniqueConstraint("round_id", "sku", "channel"),
    )
    op.create_index(
        "ix_recommendations_round_priority", "recommendations", ["round_id", "priority"]
    )
    op.create_index(
        "ix_recommendations_round_recommendation", "recommendations", ["round_id", "recommendation"]
    )

    op.create_table(
        "decisions",
        uuid_pk(),
        sa.Column(
            "recommendation_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("recommendations.id"),
            nullable=False,
        ),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", enum("decision_t"), nullable=False),
        sa.Column("applied_price", sa.Numeric(12, 2)),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("comment", sa.Text),
        sa.Column("snapshot_recommendation", enum("recommendation_t"), nullable=False),
        sa.Column("snapshot_suggested_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("snapshot_current_price", sa.Numeric(12, 2), nullable=False),
        created_at(),
    )
    op.create_index(
        "ix_decisions_recommendation_created",
        "decisions",
        ["recommendation_id", sa.text("created_at DESC")],
    )

    # Registro de decisões é append-only: bloqueia UPDATE e DELETE no banco.
    op.execute(
        """
        create function decisions_append_only() returns trigger language plpgsql as $$
        begin
          raise exception 'decisions é append-only: % não permitido', tg_op;
        end;
        $$;
        create trigger trg_decisions_append_only
          before update or delete on decisions
          for each row execute function decisions_append_only();
        """
    )


def downgrade() -> None:
    op.execute("drop trigger if exists trg_decisions_append_only on decisions")
    op.execute("drop function if exists decisions_append_only()")
    for table in (
        "decisions",
        "recommendations",
        "rounds",
        "stock_snapshot",
        "product_channel_state",
        "products",
        "users",
    ):
        op.drop_table(table)
    bind = op.get_bind()
    for name in ENUMS:
        pg.ENUM(name=name).drop(bind, checkfirst=True)
