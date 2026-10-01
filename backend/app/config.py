from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://popularpet:popularpet@localhost:5432/popularpet"
    seed_dir: str = "/seed"
    # Fuso usado em datas exibidas/exportadas (o banco guarda timestamptz)
    timezone: str = "America/Sao_Paulo"


settings = Settings()
