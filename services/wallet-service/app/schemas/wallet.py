import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    currency: str
    balance: Decimal
    locked_balance: Decimal
    available_balance: Decimal  # Computed: balance - locked_balance

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_available(cls, wallet):
        return cls(
            id=wallet.id,
            user_id=wallet.user_id,
            currency=wallet.currency,
            balance=wallet.balance,
            locked_balance=wallet.locked_balance,
            available_balance=wallet.balance - wallet.locked_balance,
        )


class TopUpRequest(BaseModel):
    user_id: uuid.UUID
    currency: str = Field(default="USDT", max_length=10)
    amount: Decimal = Field(gt=0, description="Amount to credit (must be positive)")


class TopUpResponse(BaseModel):
    user_id: uuid.UUID
    currency: str
    new_balance: Decimal
    message: str
