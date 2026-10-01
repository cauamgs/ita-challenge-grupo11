import enum

from sqlalchemy import Enum


class Channel(enum.StrEnum):
    LOJA_FISICA = "LOJA_FISICA"
    ECOMMERCE = "ECOMMERCE"
    MARKETPLACE = "MARKETPLACE"


class RecommendationType(enum.StrEnum):
    SUBIR = "SUBIR"
    BAIXAR = "BAIXAR"
    MANTER = "MANTER"
    REVISAR = "REVISAR"


class RiskLevel(enum.StrEnum):
    BAIXO = "BAIXO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class DecisionType(enum.StrEnum):
    APROVAR = "APROVAR"
    EDITAR = "EDITAR"
    REJEITAR = "REJEITAR"
    ADIAR = "ADIAR"


class UserRole(enum.StrEnum):
    ANALISTA = "ANALISTA"
    GESTOR = "GESTOR"


# Tipos PostgreSQL (criados pela migration; os models não os recriam)
channel_t = Enum(Channel, name="channel_t", create_type=False)
recommendation_t = Enum(RecommendationType, name="recommendation_t", create_type=False)
risk_t = Enum(RiskLevel, name="risk_t", create_type=False)
decision_t = Enum(DecisionType, name="decision_t", create_type=False)
user_role_t = Enum(UserRole, name="user_role_t", create_type=False)

# Rótulos em português usados no CSV/xlsx e na interface
CHANNEL_LABELS: dict[Channel, str] = {
    Channel.LOJA_FISICA: "Loja física",
    Channel.ECOMMERCE: "E-commerce",
    Channel.MARKETPLACE: "Marketplace",
}
CHANNEL_BY_LABEL: dict[str, Channel] = {v: k for k, v in CHANNEL_LABELS.items()}
RISK_BY_LABEL: dict[str, RiskLevel] = {
    "Baixo": RiskLevel.BAIXO,
    "Médio": RiskLevel.MEDIO,
    "Alto": RiskLevel.ALTO,
}
