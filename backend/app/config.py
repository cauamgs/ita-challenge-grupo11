from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://popularpet:popularpet@localhost:5432/popularpet"
    seed_dir: str = "/seed"
    # Fuso usado em datas exibidas/exportadas (o banco guarda timestamptz)
    timezone: str = "America/Sao_Paulo"
    # Integração simulada com o ERP: planilha lida em "Sincronizar agora" e nas execuções agendadas
    # (padrão: <seed_dir>/base_popular_pet.xlsx)
    erp_source_file: str | None = None
    # Agendador da sincronização automática (desligado nos testes)
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 30


settings = Settings()
