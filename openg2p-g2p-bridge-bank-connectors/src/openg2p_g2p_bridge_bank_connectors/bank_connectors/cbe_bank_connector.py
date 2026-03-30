import logging
import time
from typing import List, Optional

import httpx
from openg2p_g2p_bridge_models.models import (
    FundsAvailableWithBankEnum,
    FundsBlockedWithBankEnum,
)

from ..bank_interface.bank_connector_interface import (
    BankConnectorInterface,
    BlockFundsResponse,
    CheckFundsResponse,
    DisbursementPaymentPayload,
    PaymentResponse,
    PaymentStatus,
)
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class CBEBankConnector(BankConnectorInterface):
    _token: Optional[str] = None
    _token_expiry: float = 0

    def _get_auth_token(self) -> str:
        """Helper function to get OAuth2 token for CBE."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        _logger.info("Fetching new auth token from CBE")
        try:
            with httpx.Client(verify=False) as client:
                data = {
                    "grant_type": _config.cbe_grant_type,
                    "client_id": _config.cbe_client_id,
                    "client_secret": _config.cbe_client_secret,
                    "scope": _config.cbe_scope,
                }
                response = client.post(_config.cbe_token_url, data=data)
                response.raise_for_status()
                token_data = response.json()
                self._token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expiry = time.time() + expires_in
                return self._token
        except Exception as e:
            _logger.error(f"Failed to get auth token from CBE: {e}")
            raise

    def check_funds(self, account_number, currency, amount) -> CheckFundsResponse:
        # CBE doesn't have a specific check_funds API in the provided collection.
        # Returning success as a placeholder or implementing a mock.
        _logger.info(f"Checking funds for CBE: {account_number}, {currency}, {amount}")
        return CheckFundsResponse(
            status=FundsAvailableWithBankEnum.FUNDS_AVAILABLE, error_code=""
        )

    def block_funds(self, account_number, currency, amount) -> BlockFundsResponse:
        # CBE doesn't have a specific block_funds API in the provided collection.
        # Returning success with a mock reference.
        _logger.info(f"Blocking funds for CBE: {account_number}, {currency}, {amount}")
        return BlockFundsResponse(
            status=FundsBlockedWithBankEnum.FUNDS_BLOCK_SUCCESS,
            block_reference_no=f"CBE_BLOCK_{int(time.time())}",
            error_code="",
        )

    def initiate_payment(
        self, disbursement_payment_payloads: List[DisbursementPaymentPayload]
    ) -> PaymentResponse:
        _logger.info(f"Initiating CBE payment for {len(disbursement_payment_payloads)} disbursements")
        
        token = self._get_auth_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "CP4I-AUTHORIZATION": _config.cbe_cp4i_authorization,
            "Content-Type": "application/json",
        }

        # The API is for bulk but we use it as single transfer as requested.
        # We will loop through each payload and send it individually.
        # If all succeed, we return SUCCESS. If any fail, we might return ERROR.
        # For simplicity in this implementation, if any fail we return ERROR.
        
        try:
            with httpx.Client(verify=False) as client:
                for payload in disbursement_payment_payloads:
                    request_body = {
                        "WebRequestCommon": {
                            "company": _config.cbe_company,
                            "password": _config.cbe_password,
                            "userName": _config.cbe_user_name
                        },
                        "OfsFunction": {},
                        "FTBULKCREDITACINPUTETHWType": {
                            "DRACCOUNT": payload.remitting_account,
                            "DRCURRENCY": payload.remitting_account_currency,
                            "DRAMOUNT": str(payload.payment_amount),
                            "DRVALUEDATE": payload.payment_date.replace("-", ""),  # Assuming date might need formatting
                            "DRTHIERREF": payload.disbursement_id,
                            "CRCURRENCY": payload.beneficiary_account_currency or payload.remitting_account_currency,
                            "gCRACCOUNT": {
                                "mCRACCOUNT": [
                                    {
                                        "CRACCOUNT": payload.beneficiary_account,
                                        "CRAMOUNT": str(payload.payment_amount),
                                        "CRTHIERREF": payload.beneficiary_name or "",
                                        "@m": 1
                                    }
                                ],
                                "@g": 1
                            },
                            "gORDERINGBK": {
                                "ORDERINGBK": [
                                    payload.disbursement_narrative or "PAYMENT"
                                ],
                                "@g": 1
                            },
                            "@id": ""
                        }
                    }
                    
                    _logger.info(f"Sending payment request to CBE for disbursement_id: {payload.disbursement_id}")
                    response = client.post(_config.cbe_payment_url, headers=headers, json=request_body)
                    response.raise_for_status()
                    
                    # You might need more complex response parsing here depending on CBE's response format
                    _logger.info(f"Successfully initiated payment for {payload.disbursement_id}")

                return PaymentResponse(status=PaymentStatus.SUCCESS, error_code="")
                
        except httpx.HTTPStatusError as e:
            _logger.error(f"HTTP error occurred during CBE payment: {e.response.text}")
            return PaymentResponse(status=PaymentStatus.ERROR, error_code=str(e))
        except Exception as e:
            _logger.error(f"Unexpected error during CBE payment: {e}")
            return PaymentResponse(status=PaymentStatus.ERROR, error_code=str(e))

    def retrieve_reconciliation_id(
        self, bank_reference: str, customer_reference: str, narratives: str
    ) -> str:
        return customer_reference

    def retrieve_disbursement_id(
        self, bank_reference: str, customer_reference: str, narratives: str
    ) -> str:
        _logger.info(
            f"Retrieving disbursement id for bank_reference: {bank_reference}, customer_reference: {customer_reference}"
        )
        return customer_reference

    def retrieve_beneficiary_name(self, narratives: str) -> str:
        _logger.info(f"Retrieving beneficiary name from narratives: {narratives}")
        return narratives[3]

    def retrieve_reversal_reason(self, narratives: str) -> str:
        _logger.info(f"Retrieving reversal reason from narratives: {narratives}")
        return narratives[-1]