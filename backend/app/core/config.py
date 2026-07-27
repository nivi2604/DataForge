from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = "DataForge"
    app_version: str = "0.1.0"
    debug: bool = False


settings = Settings()
