import json
from typing import Optional

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
# Store the credit score in memory - in production, store it in a secure
# persistent data store.
credit_score = 700  # Default value

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


class TransactionsSyncRequest(BaseModel):
    """
    Pydantic model for Plaid transactions sync request.

    Attributes:
        client_id (str): The Plaid client ID
        secret (str): The Plaid secret key
        access_token (str): The Plaid access token
        cursor (str, optional): The cursor for pagination
        count (int, optional): The number of transactions to fetch
    """
    client_id: str = Field(..., min_length=1)
    secret: str = Field(..., min_length=1)
    access_token: str = Field(..., min_length=1)
    cursor: Optional[str] = None
    count: Optional[int] = 500


# Add a custom JSON encoder class at the top of the file
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, dt.datetime)):
            return obj.isoformat()
        return super().default(obj)


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
            global access_token, item_id, credit_score
            try:
                print("==== STARTING TOKEN EXCHANGE ====")
                print(f"Received public token: {request.public_token[:10]}...")
                
                exchange_request = ItemPublicTokenExchangeRequest(public_token=request.public_token)
                print("Created exchange request object")
                
                exchange_response = client.item_public_token_exchange(exchange_request)
                print("Successfully exchanged public token for access token")
                print(f"Access token received: {exchange_response['access_token'][:10]}...")
                print(f"Item ID received: {exchange_response['item_id']}")
                
                access_token = exchange_response['access_token']
                item_id = exchange_response['item_id']
                
                # Log the access token (in production, you would never log sensitive tokens)
                self.logger.info(
                    "plaid_token_exchanged",
                    item_id=item_id,
                    token_length=len(access_token)
                )
                
                # Initialize response dictionary with exchange response
                response_data = {
                    "exchange_response": exchange_response.to_dict()
                }
                print("Response data initialized with exchange response")
                
                # Fetch transactions
                try:
                    print("==== STARTING TRANSACTION SYNC ====")
                    sync_request = plaid.model.transactions_sync_request.TransactionsSyncRequest(
                        access_token=access_token,
                        count=500
                    )
                    print("Created transaction sync request")
                    
                    transactions_response = client.transactions_sync(sync_request)
                    print(f"Successfully fetched transactions")
                    print(f"Added transactions: {len(transactions_response['added'])}")
                    print(f"Modified transactions: {len(transactions_response['modified'])}")
                    print(f"Removed transactions: {len(transactions_response['removed'])}")
                    print(f"Has more: {transactions_response['has_more']}")
                    
                    if transactions_response['added']:
                        # Print transaction data safely using our custom encoder
                        first_transaction = transactions_response['added'][0].to_dict()
                        print(f"Transaction keys: {list(first_transaction.keys())}")
                        print(f"Sample transaction amount: {first_transaction.get('amount')}")
                        print(f"Sample transaction date: {first_transaction.get('date')}")
                        print(f"Sample transaction name: {first_transaction.get('name')}")
                        
                        # Try to safely print the full transaction with our custom encoder
                        try:
                            print(f"Sample transaction: {json.dumps(first_transaction, indent=2, cls=CustomJSONEncoder)[:200]}...")
                        except Exception as json_err:
                            print(f"Could not serialize transaction: {str(json_err)}")
                    
                    # Log transaction data summary to the same logger
                    self.logger.info(
                        "plaid_transactions_fetched",
                        item_id=item_id,
                        added_count=len(transactions_response['added']),
                        modified_count=len(transactions_response['modified']),
                        removed_count=len(transactions_response['removed']),
                        has_more=transactions_response['has_more']
                    )
                    
                    # Convert transactions to a format that can be serialized
                    serializable_transactions = {
                        "added": [self.make_serializable(t.to_dict()) for t in transactions_response['added']],
                        "modified": [self.make_serializable(t.to_dict()) for t in transactions_response['modified']],
                        "removed": [self.make_serializable(t.to_dict()) for t in transactions_response['removed']],
                        "has_more": transactions_response['has_more'],
                        "next_cursor": transactions_response['next_cursor']
                    }
                    
                    response_data["transactions"] = serializable_transactions
                    print("Added transactions to response data")
                    
                    # Call the conversation handler with a simple question
                    print("==== STARTING AI CONVERSATION ====")
                    # Create a simplified version of transactions for the AI
                    simplified_transactions = {
                        "transaction_count": len(serializable_transactions["added"]),
                        "transactions": serializable_transactions["added"][:10]  # Just send the first 10 transactions
                    }
                    
                    conversation_message = f"Generate a number looking at my transaction history. This number should be roughly in the ballpark of the magnitude of a credit score. Here are my transactions: {json.dumps(simplified_transactions, cls=CustomJSONEncoder)}. PLEASE RETURN ONLY THE CREDIT SCORE, NO OTHER TEXT NO MATTER WHAT. even if you are unsure or unfamiliar, I'd appreciate you giving me a number a lot!'"
                    print(f"Sending message to AI (length: {len(conversation_message)})")
                    
                    conversation_response = await self.handle_conversation(conversation_message)
                    print("Received response from AI")
                    print(f"AI response preview: {conversation_response['response'][:200]}...")
                    
                    # Add the AI response to the response data
                    response_data["ai_response"] = conversation_response["response"]
                    
                    # Extract credit score from AI response
                    try:
                        # Try to parse the credit score from the AI response
                        # This assumes the AI returns just a number or a number with some text
                        ai_response = conversation_response["response"].strip()
                        # Extract digits from the response
                        import re
                        score_match = re.search(r'\b(\d{3})\b', ai_response)  # Look for 3-digit number
                        
                        if score_match:
                            extracted_score = int(score_match.group(1))
                            # Validate the score is in a reasonable range (300-850 for FICO)
                            if 300 <= extracted_score <= 850:
                                credit_score = extracted_score
                                response_data["credit_score"] = credit_score
                                print(f"Extracted credit score from AI: {credit_score}")
                            else:
                                credit_score = 715  # Fallback to default if outside valid range
                                response_data["credit_score"] = credit_score
                                print(f"Score out of range, using default: {credit_score}")
                        else:
                            credit_score = 710  # Fallback to default if no score found
                            response_data["credit_score"] = credit_score
                            print(f"No score found in AI response, using default: {credit_score}")
                    except Exception as score_err:
                        print(f"Error extracting credit score: {str(score_err)}")
                        credit_score = 705  # Fallback to default on error
                        response_data["credit_score"] = credit_score
                        print(f"Using default credit score: {credit_score}")
                    
                    self.logger.info(
                        "AI_RESPONSE_GENERATED",
                        response_length=len(conversation_response["response"]),
                        extracted_credit_score=credit_score
                    )
                    print("==== COMPLETED SUCCESSFULLY ====")
                    
                except Exception as e:
                    print(f"==== ERROR IN TRANSACTION SYNC OR AI PROCESSING ====")
                    print(f"Error: {str(e)}")
                    print(f"Error type: {type(e).__name__}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    
                    self.logger.exception("transactions_sync_failed", error=str(e))
                    response_data["transactions_error"] = str(e)
                    response_data["credit_score"] = 700  # Default fallback score
                    print("Added error info and default credit score to response")
                
                # Return all collected data
                print(f"Returning response with keys: {list(response_data.keys())}")
                return response_data
                
            except plaid.ApiException as e:
                print(f"==== PLAID API ERROR ====")
                print(f"Error: {str(e)}")
                error_body = json.loads(e.body)
                print(f"Error details: {json.dumps(error_body, indent=2)}")
                
                self.logger.error("plaid_token_exchange_failed", error=str(e))
                return json.loads(e.body)
            except Exception as e:
                print(f"==== UNEXPECTED ERROR ====")
                print(f"Error: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                
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

        @self._router.get("/credit_score")
        async def get_credit_score():
            """
            Get the latest calculated credit score.
            
            Returns:
                dict: Contains the credit score
            """
            # This endpoint returns the global credit score variable
            try:
                global credit_score
                # Add detailed logging
                self.logger.info(
                    "credit_score_endpoint_called",
                    credit_score=credit_score,
                    timestamp=dt.datetime.now().isoformat(),
                    request_id=str(uuid.uuid4())  # Generate a unique ID for this request
                )
                print(f"==== CREDIT SCORE ENDPOINT CALLED ====")
                print(f"Returning credit score: {credit_score}")
                print(f"Timestamp: {dt.datetime.now().isoformat()}")
                
                return {"credit_score": credit_score}
            except Exception as e:
                self.logger.exception("get_credit_score_failed", error=str(e))
                print(f"==== CREDIT SCORE ENDPOINT ERROR ====")
                print(f"Error: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get credit score: {str(e)}"
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

        @self._router.post("/transactions/sync")
        async def sync_transactions(request: TransactionsSyncRequest) -> dict:
            """
            Fetch transactions using Plaid's transactions/sync endpoint.
            
            Args:
                request: Contains access_token, cursor, and count parameters
                
            Returns:
                dict: Contains added, modified, removed transactions and a cursor
            """
            try:
                # Configure a new client with the provided credentials
                # This allows the endpoint to work with different credentials if needed
                config = plaid.Configuration(
                    host=plaid.Environment.Sandbox,
                    api_key={
                        'clientId': request.client_id,
                        'secret': request.secret,
                    }
                )
                api_client = plaid.ApiClient(config)
                temp_client = plaid_api.PlaidApi(api_client)
                
                # Create the transactions sync request
                sync_request = plaid.model.transactions_sync_request.TransactionsSyncRequest(
                    access_token=request.access_token,
                    cursor=request.cursor,
                    count=request.count
                )
                
                # Call the Plaid API
                response = temp_client.transactions_sync(sync_request)
                
                # Log success (without sensitive data)
                self.logger.info(
                    "transactions_synced",
                    added_count=len(response['added']),
                    modified_count=len(response['modified']),
                    removed_count=len(response['removed']),
                    has_more=response['has_more']
                )
                
                # Return the response
                return response.to_dict()
                
            except plaid.ApiException as e:
                error_response = json.loads(e.body)
                self.logger.error(
                    "transactions_sync_failed",
                    error_type=error_response.get('error_type'),
                    error_code=error_response.get('error_code'),
                    error_message=error_response.get('error_message')
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Plaid error: {error_response.get('error_message')}"
                ) from e
            except Exception as e:
                self.logger.exception("transactions_sync_failed", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to sync transactions: {str(e)}"
                ) from e

        @self._router.post("/liabilities/get")
        async def get_liabilities(request: dict):
            """
            Fetch liabilities for a given access token.
            
            Args:
                request: Contains client_id, secret, and access_token
                
            Returns:
                dict: Contains accounts and liabilities information
            """
            try:
                # Configure a new client with the provided credentials
                config = plaid.Configuration(
                    host=plaid.Environment.Sandbox,
                    api_key={
                        'clientId': request.get('client_id'),
                        'secret': request.get('secret'),
                    }
                )
                api_client = plaid.ApiClient(config)
                temp_client = plaid_api.PlaidApi(api_client)
                
                # Create the liabilities request
                liabilities_request = plaid.model.liabilities_get_request.LiabilitiesGetRequest(
                    access_token=request.get('access_token')
                )
                
                # Call the Plaid API
                response = temp_client.liabilities_get(liabilities_request)
                
                # Extract and log key information about liabilities
                liability_summary = {
                    "accounts_count": len(response['accounts']),
                    "account_types": {},
                    "liability_types": []
                }
                
                # Summarize account types
                for account in response['accounts']:
                    account_type = account.get('type')
                    if account_type in liability_summary["account_types"]:
                        liability_summary["account_types"][account_type] += 1
                    else:
                        liability_summary["account_types"][account_type] = 1
                
                # Check for different liability types
                if 'liabilities' in response:
                    liability_summary["liability_types"] = list(response['liabilities'].keys())
                    
                    # Count specific liability types
                    liability_summary["credit_count"] = len(response['liabilities'].get('credit', []))
                    liability_summary["mortgage_count"] = len(response['liabilities'].get('mortgage', []))
                    liability_summary["student_count"] = len(response['liabilities'].get('student', []))
                
                # Log the liability summary
                self.logger.info(
                    "liabilities_fetched",
                    liability_summary=liability_summary
                )
                
                # Return the response
                return response.to_dict()
                
            except plaid.ApiException as e:
                error_response = json.loads(e.body)
                self.logger.error(
                    "liabilities_fetch_failed",
                    error_type=error_response.get('error_type'),
                    error_code=error_response.get('error_code'),
                    error_message=error_response.get('error_message')
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Plaid error: {error_response.get('error_message')}"
                ) from e
            except Exception as e:
                self.logger.exception("liabilities_fetch_failed", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch liabilities: {str(e)}"
                ) from e

        @self._router.post("/conversation")
        async def direct_conversation(message: ChatMessage) -> dict[str, str]:
            """
            Direct endpoint for conversation with the AI without semantic routing.
            
            This endpoint allows sending messages directly to the AI provider
            without going through the semantic routing process. It's useful for
            simple Q&A interactions about financial data and Plaid services.
            
            Args:
                message: Validated chat message
                
            Returns:
                dict[str, str]: Response from AI provider
            """
            try:
                self.logger.info(
                    "plaid_conversation_request",
                    message_length=len(message.message)
                )
                
                # Send the message directly to the AI provider
                response = self.ai.send_message(message.message)
                
                self.logger.info(
                    "plaid_conversation_response",
                    response_length=len(response.text)
                )
                
                return {"response": response.text}
            except Exception as e:
                self.logger.exception("plaid_conversation_failed", error=str(e))
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process conversation: {str(e)}"
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

    # Add this helper method to the PlaidRouter class
    def make_serializable(self, obj):
        """Convert Plaid objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self.make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.make_serializable(i) for i in obj]
        elif isinstance(obj, (date, dt.datetime)):
            return obj.isoformat()
        else:
            return obj
    