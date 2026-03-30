from openg2p_fastapi_common.service import BaseService

from ..bank_interface.bank_connector_interface import BankConnectorInterface
from ..config import Settings
from .cbe_bank_connector import CBEBankConnector

_config = Settings.get_config()


class BankConnectorFactory(BaseService):
    def get_bank_connector(self, sponsor_bank_code: str) -> BankConnectorInterface:
        if sponsor_bank_code == _config.bank_simulator_code:
            return CBEBankConnector()
        else:
            raise NotImplementedError(
                f"Bank {sponsor_bank_code} is not supported. Supported bank: {_config.bank_simulator_code}"
            )
