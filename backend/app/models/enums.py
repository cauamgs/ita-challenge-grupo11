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


class SyncTrigger(enum.StrEnum):
    INICIAL = "INICIAL"  # carga inicial no seed
    MANUAL = "MANUAL"  # botão "Sincronizar agora"
    AGENDADO = "AGENDADO"  # sincronização automática
    ARQUIVO = "ARQUIVO"  # upload de arquivo exportado do ERP


class SyncStatus(enum.StrEnum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    SUCESSO = "SUCESSO"
    ERRO = "ERRO"


class SyncFrequency(enum.StrEnum):
    DIARIA = "DIARIA"
    SEMANAL = "SEMANAL"
    MENSAL = "MENSAL"


class PriceChangeType(enum.StrEnum):
    INICIAL = "INICIAL"  # primeiro preço conhecido do SKU no canal
    AUMENTO = "AUMENTO"
    REDUCAO = "REDUCAO"


# Tipos PostgreSQL (criados pela migration; os models não os recriam)
channel_t = Enum(Channel, name="channel_t", create_type=False)
recommendation_t = Enum(RecommendationType, name="recommendation_t", create_type=False)
risk_t = Enum(RiskLevel, name="risk_t", create_type=False)
decision_t = Enum(DecisionType, name="decision_t", create_type=False)
user_role_t = Enum(UserRole, name="user_role_t", create_type=False)
sync_trigger_t = Enum(SyncTrigger, name="sync_trigger_t", create_type=False)
sync_status_t = Enum(SyncStatus, name="sync_status_t", create_type=False)
sync_frequency_t = Enum(SyncFrequency, name="sync_frequency_t", create_type=False)
price_change_t = Enum(PriceChangeType, name="price_change_t", create_type=False)

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
