import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..models.order import ExecutionMode, MarketType, OrderSide, OrderStatus, OrderType


class OrderFillResponse(BaseModel):
    id: uuid.UUID
    fill_price: Decimal
    fill_quantity: Decimal
    fee: Decimal
    fee_currency: str
    execution_mode: ExecutionMode
    filled_at: str

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    side: OrderSide
    order_type: OrderType
    market_type: MarketType
    quantity: Decimal
    price: Optional[Decimal]
    stop_price: Optional[Decimal]
    leverage: Optional[int]
    reduce_only: bool
    status: OrderStatus
    execution_mode: ExecutionMode
    external_order_id: Optional[str]
    created_at: str
    updated_at: str
    fills: List[OrderFillResponse] = []

    model_config = {"from_attributes": True}


class PlaceOrderRequest(BaseModel):
    symbol: str = Field(max_length=20, description="e.g. BTC/USDT")
    side: OrderSide
    order_type: OrderType
    market_type: MarketType = MarketType.SPOT
    quantity: Decimal = Field(gt=0)
    price: Optional[Decimal] = Field(default=None, gt=0)
    stop_price: Optional[Decimal] = Field(default=None, gt=0)
    leverage: Optional[int] = Field(default=None, ge=1, le=125)
    reduce_only: bool = False

    def validate_price(self) -> None:
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("price is required for LIMIT orders")
        if self.order_type in (OrderType.STOP_LOSS, OrderType.TAKE_PROFIT) and self.stop_price is None:
            raise ValueError("stop_price is required for STOP_LOSS / TAKE_PROFIT orders")
        if self.market_type == MarketType.FUTURES and self.leverage is None:
            raise ValueError("leverage is required for FUTURES orders")


class PlaceOrderResponse(BaseModel):
    order_id: uuid.UUID
    status: OrderStatus
    message: str
