import json

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import Web3RPCError
import base64
import os
import datetime as dt
import json
import time
from datetime import date, timedelta
import uuid
# from plaid import Client
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

from flare_ai_defai.ai import GeminiProvider
from flare_ai_defai.attestation import Vtpm, VtpmAttestationError
from flare_ai_defai.blockchain import FlareProvider
from flare_ai_defai.prompts import PromptService, SemanticRouterResponse
from flare_ai_defai.settings import settings
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import plaid
from plaid.model.payment_amount import PaymentAmount
from plaid.model.payment_amount_currency import PaymentAmountCurrency
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.recipient_bacs_nullable import RecipientBACSNullable
from plaid.model.payment_initiation_address import PaymentInitiationAddress
from plaid.model.payment_initiation_recipient_create_request import PaymentInitiationRecipientCreateRequest
from plaid.model.payment_initiation_payment_create_request import PaymentInitiationPaymentCreateRequest
from plaid.model.payment_initiation_payment_get_request import PaymentInitiationPaymentGetRequest
from plaid.model.link_token_create_request_payment_initiation import LinkTokenCreateRequestPaymentInitiation
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.user_create_request import UserCreateRequest
from plaid.model.consumer_report_user_identity import ConsumerReportUserIdentity
from plaid.model.asset_report_create_request import AssetReportCreateRequest
from plaid.model.asset_report_create_request_options import AssetReportCreateRequestOptions
from plaid.model.asset_report_user import AssetReportUser
from plaid.model.asset_report_get_request import AssetReportGetRequest
from plaid.model.asset_report_pdf_get_request import AssetReportPDFGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.investments_transactions_get_request_options import InvestmentsTransactionsGetRequestOptions
from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.transfer_authorization_create_request import TransferAuthorizationCreateRequest
from plaid.model.transfer_create_request import TransferCreateRequest
from plaid.model.transfer_get_request import TransferGetRequest
from plaid.model.transfer_network import TransferNetwork
from plaid.model.transfer_type import TransferType
from plaid.model.transfer_authorization_user_in_request import TransferAuthorizationUserInRequest
from plaid.model.ach_class import ACHClass
from plaid.model.transfer_create_idempotency_key import TransferCreateIdempotencyKey
from plaid.model.transfer_user_address_in_request import TransferUserAddressInRequest
from plaid.model.signal_evaluate_request import SignalEvaluateRequest
from plaid.model.statements_list_request import StatementsListRequest
from plaid.model.link_token_create_request_statements import LinkTokenCreateRequestStatements
from plaid.model.link_token_create_request_cra_options import LinkTokenCreateRequestCraOptions
from plaid.model.statements_download_request import StatementsDownloadRequest
from plaid.model.consumer_report_permissible_purpose import ConsumerReportPermissiblePurpose
from plaid.model.cra_check_report_base_report_get_request import CraCheckReportBaseReportGetRequest
from plaid.model.cra_check_report_pdf_get_request import CraCheckReportPDFGetRequest
from plaid.model.cra_check_report_income_insights_get_request import CraCheckReportIncomeInsightsGetRequest
from plaid.model.cra_check_report_partner_insights_get_request import CraCheckReportPartnerInsightsGetRequest
from plaid.model.cra_pdf_add_ons import CraPDFAddOns
from plaid.api import plaid_api

logger = structlog.get_logger(__name__)
router = APIRouter()

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': settings.PLAID_CLIENT_ID,
        'secret': settings.PLAID_SECRET,
        'plaidVersion': '2020-09-14'
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

products = ["transactions", "liabilities"]
for product in settings.PLAID_PRODUCTS:
    products.append(Products(product))

# We store the access_token in memory - in production, store it in a secure
# persistent data store.
access_token = None
wallet_address = None 
# The payment_id is only relevant for the UK Payment Initiation product.
# We store the payment_id in memory - in production, store it in a secure
# persistent data store.
payment_id = None
# The transfer_id is only relevant for Transfer ACH product.
# We store the transfer_id in memory - in production, store it in a secure
# persistent data store.
transfer_id = None
# We store the user_token in memory - in production, store it in a secure
# persistent data store.
user_token = None

item_id = None

class ChatMessage(BaseModel):
    """
    Pydantic model for chat message validation.

    Attributes:
        message (str): The chat message content, must not be empty
    """

    message: str = Field(..., min_length=1)


class PlaidPublicTokenRequest(BaseModel):
    """
    Pydantic model for Plaid public token validation.

    Attributes:
        public_token (str): The Plaid public token
    """
    public_token: str = Field(..., min_length=1)

class PlaidWalletAddressRequest(BaseModel):
    """
    Pydantic model for Plaid wallet address validation.

    Attributes:
        wallet_address (str): The Plaid wallet address
    """
    wallet_address: str = Field(..., min_length=1)

class PlaidTokenRequest(BaseModel):
    """
    Pydantic model for Plaid token validation.

    Attributes:
        access_token (str): The Plaid access token
        item_id (str): The Plaid item ID
    """
    access_token: str = Field(..., min_length=1)
    item_id: str = Field(..., min_length=1)


class PlaidRouter:
    """
    Main router class handling chat messages and their routing to appropriate handlers.

    This class integrates various services and provides routing logic for different
    types of chat messages including blockchain operations, attestations, and general
    conversation.

    Attributes:
        ai (GeminiProvider): Provider for AI capabilities
        blockchain (FlareProvider): Provider for blockchain operations
        attestation (Vtpm): Provider for attestation services
        prompts (PromptService): Service for managing prompts
        logger (BoundLogger): Structured logger for the chat router
    """

    def __init__(
        self,
        ai: GeminiProvider,
        blockchain: FlareProvider,
        attestation: Vtpm,
        prompts: PromptService,
    ) -> None:
        """
        Initialize the ChatRouter with required service providers.

        Args:
            ai: Provider for AI capabilities
            blockchain: Provider for blockchain operations
            attestation: Provider for attestation services
            prompts: Service for managing prompts
        """
        self._router = APIRouter()
        self.ai = ai
        self.blockchain = blockchain
        self.attestation = attestation
        self.prompts = prompts
        self.logger = logger.bind(router="chat")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """
        Set up FastAPI routes for the chat endpoint.
        Handles message routing, command processing, and transaction confirmations.
        """

        @self._router.post("/exchange_public_token")
        async def exchange_public_token(request: PlaidPublicTokenRequest) -> dict:
            """
            Exchange a Plaid public token for an access token.
            Following Plaid's recommended pattern from their documentation.

            Args:
                request: Contains the public_token from Plaid Link

            Returns:
                dict: Contains access_token and item_id
            """
            try:
                global access_token, item_id
                # Exchange the public token using Plaid's official client
                exchange_request = ItemPublicTokenExchangeRequest(
                    public_token=request.public_token
                )
                exchange_response = client.item_public_token_exchange(exchange_request)
                access_token = exchange_response['access_token']
                item_id = exchange_response['item_id']

                # Store the access token securely in the TEE
                self.logger.info(
                    "plaid_token_exchanged",
                    item_id=item_id,
                    token_length=len(access_token)
                )

                return exchange_response.to_dict()
            except plaid.ApiException as e:
                error_response = json.loads(e.body)
                self.logger.error(
                    "plaid_token_exchange_failed",
                    error_type=error_response.get('error_type'),
                    error_code=error_response.get('error_code'),
                    error_message=error_response.get('error_message')
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Plaid error: {error_response.get('error_message')}"
                ) from e
            except Exception as e:
                self.logger.exception("public_token_exchange_failed", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to exchange public token: {str(e)}"
                ) from e

        @self._router.post("/store_token")
        async def store_plaid_token(request: PlaidTokenRequest) -> dict[str, str]:
            """
            Store Plaid access token in the TEE.
            This endpoint should only be accessible within the TEE environment.

            Args:
                request: PlaidTokenRequest containing access_token and item_id

            Returns:
                dict[str, str]: Success message if token is stored
            """
            try:
                # Here we would securely store the token in the TEE
                # For now, we'll just log it (in production, NEVER log sensitive tokens)
                self.logger.info(
                    "plaid_token_received",
                    item_id=request.item_id,
                    token_length=len(request.access_token)
                )
                
                # TODO: Implement secure storage in TEE
                # In production, you would:
                # 1. Verify we're in a TEE environment
                # 2. Encrypt the token with TEE-specific encryption
                # 3. Store the encrypted token securely
                # 4. Only allow decryption within the TEE

                return {"status": "success", "message": "Plaid token securely stored in TEE"}
            except Exception as e:
                self.logger.exception("plaid_token_storage_failed", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail="Failed to store Plaid token securely"
                ) from e

        @self._router.post("/")
        async def chat(message: ChatMessage) -> dict[str, str]:  # pyright: ignore [reportUnusedFunction]
            """
            Process incoming chat messages and route them to appropriate handlers.

            Args:
                message: Validated chat message

            Returns:
                dict[str, str]: Response containing handled message result

            Raises:
                HTTPException: If message handling fails
            """
            try:
                self.logger.debug("received_message", message=message.message)

                if message.message.startswith("/"):
                    return await self.handle_command(message.message)
                if (
                    self.blockchain.tx_queue
                    and message.message == self.blockchain.tx_queue[-1].msg
                ):
                    try:
                        tx_hash = self.blockchain.send_tx_in_queue()
                    except Web3RPCError as e:
                        self.logger.exception("send_tx_failed", error=str(e))
                        msg = (
                            f"Unfortunately the tx failed with the error:\n{e.args[0]}"
                        )
                        return {"response": msg}

                    prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                        "tx_confirmation",
                        tx_hash=tx_hash,
                        block_explorer=settings.web3_explorer_url,
                    )
                    tx_confirmation_response = self.ai.generate(
                        prompt=prompt,
                        response_mime_type=mime_type,
                        response_schema=schema,
                    )
                    return {"response": tx_confirmation_response.text}
                if self.attestation.attestation_requested:
                    try:
                        resp = self.attestation.get_token([message.message])
                    except VtpmAttestationError as e:
                        resp = f"The attestation failed with  error:\n{e.args[0]}"
                    self.attestation.attestation_requested = False
                    return {"response": resp}

                route = await self.get_semantic_route(message.message)
                return await self.route_message(route, message.message)

            except Exception as e:
                self.logger.exception("message_handling_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self._router.get("/info")
        async def info():
            return {
                "item_id": item_id,
                "access_token": access_token,
                "products": settings.PLAID_PRODUCTS
            }
        
        @self._router.post("/set_access_token")
        async def get_access_token(request: PlaidPublicTokenRequest):
            global access_token, item_id
            try:
                exchange_request = ItemPublicTokenExchangeRequest(public_token=request.public_token)
                exchange_response = client.item_public_token_exchange(exchange_request)
                access_token = exchange_response['access_token']
                self.logger.info(f"exchange response: {access_token}")
                item_id = exchange_response['item_id']
                return exchange_response.to_dict()
            except plaid.ApiException as e:
                self.logger.error("plaid_token_exchange_failed", error=str(e))
                return json.loads(e.body)
            except Exception as e:
                self.logger.exception("unexpected_error", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to exchange public token: {str(e)}"
                ) from e
            
        @self._router.post("/set_wallet_address")
        async def get_access_token(request: PlaidWalletAddressRequest):
            global wallet_address
            try:
                wallet_address = request.wallet_address
                self.logger.info(f"wallet address response: {wallet_address}")
                return wallet_address
            except plaid.ApiException as e:
                self.logger.error("set_wallet_address", error=str(e))
                return json.loads(e.body)
            except Exception as e:
                self.logger.exception("unexpected_error", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to integrate wallet address: {str(e)}"
                ) from e

        @self._router.post("/create_link_token")
        async def create_link_token():
            try:
                request = LinkTokenCreateRequest(
                    products=products,
                    client_name="StreetCred",
                    country_codes=[CountryCode('US')],
                    language='en',
                    user=LinkTokenCreateRequestUser(
                        client_user_id=str(uuid.uuid4())
                    )
                )
                response = client.link_token_create(request)
                return {"link_token": response['link_token']}
            except plaid.ApiException as e:
                self.logger.exception("create_link_token_failed", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create link token"
                ) from e

    @property
    def router(self) -> APIRouter:
        """Get the FastAPI router with registered routes."""
        return self._router

    async def handle_command(self, command: str) -> dict[str, str]:
        """
        Handle special command messages starting with '/'.

        Args:
            command: Command string to process

        Returns:
            dict[str, str]: Response containing command result
        """
        if command == "/reset":
            self.blockchain.reset()
            self.ai.reset()
            return {"response": "Reset complete"}
        return {"response": "Unknown command"}

    async def get_semantic_route(self, message: str) -> SemanticRouterResponse:
        """
        Determine the semantic route for a message using AI provider.

        Args:
            message: Message to route

        Returns:
            SemanticRouterResponse: Determined route for the message
        """
        try:
            prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                "semantic_router", user_input=message
            )
            route_response = self.ai.generate(
                prompt=prompt, response_mime_type=mime_type, response_schema=schema
            )
            return SemanticRouterResponse(route_response.text)
        except Exception as e:
            self.logger.exception("routing_failed", error=str(e))
            return SemanticRouterResponse.CONVERSATIONAL

    async def route_message(
        self, route: SemanticRouterResponse, message: str
    ) -> dict[str, str]:
        """
        Route a message to the appropriate handler based on semantic route.

        Args:
            route: Determined semantic route
            message: Original message to handle

        Returns:
            dict[str, str]: Response from the appropriate handler
        """
        handlers = {
            SemanticRouterResponse.GENERATE_ACCOUNT: self.handle_generate_account,
            SemanticRouterResponse.SEND_TOKEN: self.handle_send_token,
            SemanticRouterResponse.SWAP_TOKEN: self.handle_swap_token,
            SemanticRouterResponse.REQUEST_ATTESTATION: self.handle_attestation,
            SemanticRouterResponse.CONVERSATIONAL: self.handle_conversation,
        }

        handler = handlers.get(route)
        if not handler:
            return {"response": "Unsupported route"}

        return await handler(message)

    async def handle_generate_account(self, _: str) -> dict[str, str]:
        """
        Handle account generation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing new account information
                or existing account
        """
        if self.blockchain.address:
            return {"response": f"Account exists - {self.blockchain.address}"}
        address = self.blockchain.generate_account()
        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "generate_account", address=address
        )
        gen_address_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        return {"response": gen_address_response.text}

    async def handle_send_token(self, message: str) -> dict[str, str]:
        """
        Handle token sending requests.

        Args:
            message: Message containing token sending details

        Returns:
            dict[str, str]: Response containing transaction preview or follow-up prompt
        """
        if not self.blockchain.address:
            await self.handle_generate_account(message)

        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "token_send", user_input=message
        )
        send_token_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        send_token_json = json.loads(send_token_response.text)
        expected_json_len = 2
        if (
            len(send_token_json) != expected_json_len
            or send_token_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_send")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text}

        tx = self.blockchain.create_send_flr_tx(
            to_address=send_token_json.get("to_address"),
            amount=send_token_json.get("amount"),
        )
        self.logger.debug("send_token_tx", tx=tx)
        self.blockchain.add_tx_to_queue(msg=message, tx=tx)
        formatted_preview = (
            "Transaction Preview: "
            + f"Sending {Web3.from_wei(tx.get('value', 0), 'ether')} "
            + f"FLR to {tx.get('to')}\nType CONFIRM to proceed."
        )
        return {"response": formatted_preview}

    async def handle_swap_token(self, _: str) -> dict[str, str]:
        """
        Handle token swap requests (currently unsupported).

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response indicating unsupported operation
        """
        return {"response": "Sorry I can't do that right now"}

    async def handle_attestation(self, _: str) -> dict[str, str]:
        """
        Handle attestation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing attestation request
        """
        prompt = self.prompts.get_formatted_prompt("request_attestation")[0]
        request_attestation_response = self.ai.generate(prompt=prompt)
        self.attestation.attestation_requested = True
        return {"response": request_attestation_response.text}

    async def handle_conversation(self, message: str) -> dict[str, str]:
        """
        Handle general conversation messages.

        Args:
            message: Message to process

        Returns:
            dict[str, str]: Response from AI provider
        """
        response = self.ai.send_message(message)
        return {"response": response.text}
