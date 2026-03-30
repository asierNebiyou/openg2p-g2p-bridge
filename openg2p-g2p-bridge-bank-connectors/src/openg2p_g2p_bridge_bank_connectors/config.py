from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="g2p_bridge_bank_connectors_", env_file=".env", extra="allow"
    )

    db_dbname: str = "openg2p_g2p_bridge_db"

    cbe_token_url: str = (
        "https://cp4idevdpgwlb.cbe.com.et:443/cbe-dev/sandbox/mowsa-t24-oauth2/oauth2/token"
    )
    cbe_payment_url: str = (
        "https://cp4idevdpgwlb.cbe.com.et:443/cbe-dev/sandbox/mowsa-t24/WSSINGLEDEBIT"
    )
    cbe_client_id: str = "143a07ee2a04ece11e66632a3f704d0c"
    cbe_client_secret: str = "3dad7ca98bc709d8d5dd5768fbb75c46"
    cbe_scope: str = "Mowsa-T24-scope"
    cbe_grant_type: str = "client_credentials"
    cbe_cp4i_authorization: str = "Basic Q1A0OkNQNElQQVNT"
    cbe_user_name: str = "ETB029856"
    cbe_password: str = "852456"
    cbe_company: str = ""
    bank_simulator_code: str = "CBE"
