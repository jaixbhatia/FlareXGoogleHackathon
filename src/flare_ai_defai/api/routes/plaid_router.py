"""
Plaid Router Module

This module handles Plaid API interactions, including retrieving account information,
transaction history, and token management.

The module provides a PlaidRouter class that integrates:
- Plaid API interactions
- Secure token handling
- Transaction history retrieval
"""

import os
import json
import structlog
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid import Configuration, Environment, ApiClient

# Load environment variables from .env
load_dotenv()

# Retrieve Plaid API credentials from .env
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").lower()

# Validate credentials
if not PLAID_CLIENT_ID or not PLAID_SECRET:
    raise ValueError("Missing Plaid API credentials! Check your .env file.")

# Configure Plaid API
environment = {
    "sandbox": Environment.Sandbox,
    "development": getattr(Environment, "Development", Environment.Sandbox),  # Fallback
    "production": Environment.Production,
}.get(PLAID_ENV, Environment.Sandbox)

configuration = Configuration(
    host=environment,
    api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET}
)

logger = structlog.get_logger(__name__)
router = APIRouter()


class PlaidLinkTokenRequest(BaseModel):
    """Pydantic model for Plaid link token request."""
    client_user_id: str = Field(..., min_length=1)


class PlaidPublicTokenRequest(BaseModel):
    """Pydantic model for exchanging public token."""
    public_token: str = Field(..., min_length=1)


class PlaidRouter:
    """
    Router class for handling Plaid API endpoints.

    Attributes:
        client (plaid_api.PlaidApi): Plaid API client
        logger (BoundLogger): Structured logger
    """

    def __init__(self) -> None:
        """
        Initialize the PlaidRouter with Plaid API configurations.
        """
        self._router = APIRouter()
        self.logger = logger.bind(router="plaid")
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

        # Store access token in memory (for demo; use a database in production)
        self.access_token = None

        # Setup FastAPI routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """
        Set up FastAPI routes for Plaid API endpoints.
        """

        @self._router.post("/create_link_token")
        async def create_link_token(request: PlaidLinkTokenRequest) -> dict[str, str]:
            """
            Create a Plaid link token for frontend authentication.

            Args:
                request: Request containing `client_user_id`.

            Returns:
                dict[str, str]: Response with the generated link token.

            Raises:
                HTTPException: If token creation fails.
            """
            try:
                self.logger.debug("Creating link token", client_user_id=request.client_user_id)
                link_token_request = LinkTokenCreateRequest(
                    client_name="Flare AI DeFAI",
                    client_id=PLAID_CLIENT_ID,
                    secret=PLAID_SECRET,
                    country_codes=[CountryCode.US],
                    language="en",
                    user={"client_user_id": request.client_user_id},
                    products=[Products.TRANSACTIONS]
                )
                response = self.client.link_token_create(link_token_request)
                return {"link_token": response["link_token"]}
            except Exception as e:
                self.logger.exception("Failed to create link token", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to create link token")

        @self._router.post("/exchange_public_token")
        async def exchange_public_token(request: PlaidPublicTokenRequest) -> dict[str, str]:
            """
            Exchange a public token for an access token.

            Args:
                request: Request containing `public_token`.

            Returns:
                dict[str, str]: Response with the access token.

            Raises:
                HTTPException: If token exchange fails.
            """
            try:
                self.logger.debug("Exchanging public token")
                exchange_request = ItemPublicTokenExchangeRequest(public_token=request.public_token)
                response = self.client.item_public_token_exchange(exchange_request)
                self.access_token = response["access_token"]
                return {"access_token": self.access_token}
            except Exception as e:
                self.logger.exception("Failed to exchange public token", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to exchange public token")

        @self._router.get("/accounts_balance")
        async def get_accounts_balance() -> dict[str, str]:
            """
            Retrieve account balances.

            Returns:
                dict[str, str]: Response with account balance details.

            Raises:
                HTTPException: If retrieval fails.
            """
            if not self.access_token:
                raise HTTPException(status_code=400, detail="Access token not found")

            try:
                self.logger.debug("Fetching account balances")
                balance_request = AccountsBalanceGetRequest(access_token=self.access_token)
                response = self.client.accounts_balance_get(balance_request)
                return {"accounts": response["accounts"]}
            except Exception as e:
                self.logger.exception("Failed to fetch account balances", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to fetch account balances")

        @self._router.get("/transactions")
        async def get_transactions() -> dict[str, str]:
            """
            Retrieve transaction history.

            Returns:
                dict[str, str]: Response with transaction details.

            Raises:
                HTTPException: If retrieval fails.
            """
            if not self.access_token:
                raise HTTPException(status_code=400, detail="Access token not found")

            try:
                self.logger.debug("Fetching transactions")
                transactions_request = TransactionsSyncRequest(access_token=self.access_token)
                response = self.client.transactions_sync(transactions_request)
                return {"transactions": response["added"]}
            except Exception as e:
                self.logger.exception("Failed to fetch transactions", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to fetch transactions")

    @property
    def router(self) -> APIRouter:
        """Get the FastAPI router with registered routes."""
        return self._router
    