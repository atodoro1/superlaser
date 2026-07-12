from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    coinbase_key_id: str = Field(validation_alias="COINBASE_KEY_ID")
    coinbase_private_key: str = Field(validation_alias="COINBASE_PRIVATE_KEY")
    ws_api_url: str = "wss://advanced-trade-ws.coinbase.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = AppSettings()