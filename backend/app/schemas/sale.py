from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_validator


class SaleCreate(BaseModel):
    product_id: int
    quantity: int
    sold_at: Optional[datetime] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_cost_price: Decimal
    unit_selling_price: Decimal
    sold_at: datetime
    created_at: datetime

    @computed_field
    @property
    def line_total(self) -> Decimal:
        return self.unit_selling_price * self.quantity

    @computed_field
    @property
    def line_profit(self) -> Decimal:
        return (self.unit_selling_price - self.unit_cost_price) * self.quantity
