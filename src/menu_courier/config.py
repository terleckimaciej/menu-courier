from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    fb_page_access_token: str
    fb_graph_api_version: str = "v21.0"
    apify_api_token: str
    timezone: str = "Europe/Warsaw"


settings = Settings()
