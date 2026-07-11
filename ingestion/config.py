from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    # Pydantic automatically looks for these environment variables (or inside .env)
    api_key: str
    signing_key: str
    ws_api_url: str = "wss://advanced-trade-ws.coinbase.com"

    # Strict configuration to look for a local .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = AppSettings()
