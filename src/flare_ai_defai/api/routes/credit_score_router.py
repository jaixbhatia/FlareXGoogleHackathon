from fastapi import APIRouter
from pydantic import BaseModel

class UserRequest(BaseModel):
    userId: str  # Placeholder for now

class CreditScoreRouter:
    """
    Handles credit score-related API endpoints.
    """
    def __init__(self):
        """
        Initializes the credit score router.
        """
        self._router = APIRouter()

        # Define routes
        self._router.post("/get-credit-score", tags=["credit-score"])(self.get_credit_score)

    @staticmethod
    async def get_credit_score(request: UserRequest) -> dict[str, int]:
        """
        Simulates retrieving a credit score from the TEE.
        """
        credit_score = 750  # Placeholder score (eventually from Plaid + Flare)
        return {"credit_score": credit_score}

    @property
    def router(self) -> APIRouter:
        """
        Exposes the router instance.
        """
        return self._router