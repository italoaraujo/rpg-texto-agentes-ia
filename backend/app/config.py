import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # As variáveis são carregadas automaticamente do .env (se existir) ou do ambiente do SO/Docker
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    ENVIRONMENT: str = "development"
    
    # Configurações de LLM
    PRIMARY_MODEL: str = "deepseek-chat"
    FALLBACK_MODEL: str = "gpt-4o-mini"
    
    DEEPSEEK_TIMEOUT: float = 4.0  # Limite de latência conforme especificação
    FALLBACK_TIMEOUT: float = 8.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Se não estiverem setadas e não estivermos em testes, avisa o desenvolvedor
if not settings.DEEPSEEK_API_KEY:
    print("[WARNING] DEEPSEEK_API_KEY não configurada. O backend pode falhar ao contatar a API principal.")
if not settings.OPENAI_API_KEY:
    print("[WARNING] OPENAI_API_KEY não configurada. O fallback automático pode falhar.")
