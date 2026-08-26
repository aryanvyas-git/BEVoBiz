from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# products.cost_price/selling_price are NUMERIC(12, 2) columns — 10 digits
# before the decimal point. Rejecting anything past that here up front
# turns a would-be Postgres numeric-overflow error (an opaque 500) into a
# clean 422 with a real message.
MAX_PRICE = Decimal("9999999999.99")
MAX_QUANTITY = 10_000_000


class ProductCreate(BaseModel):
    name: str = Field(max_length=200)
    category: Optional[str] = Field(default=None, max_length=100)
    cost_price: Decimal
    selling_price: Decimal
    quantity_in_stock: int = 0

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()

    @field_validator("category")
    @classmethod
    def category_strip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None

    @field_validator("cost_price", "selling_price")
    @classmethod
    def price_in_range(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("price must be >= 0")
        if v > MAX_PRICE:
            raise ValueError(f"price must be <= {MAX_PRICE}")
        return v

    @field_validator("quantity_in_stock")
    @classmethod
    def quantity_in_range(cls, v: int) -> int:
        if v < 0:
            raise ValueError("quantity_in_stock must be >= 0")
        if v > MAX_QUANTITY:
            raise ValueError(f"quantity_in_stock must be <= {MAX_QUANTITY}")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    category: Optional[str] = Field(default=None, max_length=100)
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    quantity_in_stock: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()

    @field_validator("category")
    @classmethod
    def category_strip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None

    @field_validator("cost_price", "selling_price")
    @classmethod
    def price_in_range(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is None:
            return v
        if v < 0:
            raise ValueError("price must be >= 0")
        if v > MAX_PRICE:
            raise ValueError(f"price must be <= {MAX_PRICE}")
        return v

    @field_validator("quantity_in_stock")
    @classmethod
    def quantity_in_range(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 0:
            raise ValueError("quantity_in_stock must be >= 0")
        if v > MAX_QUANTITY:
            raise ValueError(f"quantity_in_stock must be <= {MAX_QUANTITY}")
        return v


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    name: str
    category: Optional[str]
    cost_price: Decimal
    selling_price: Decimal
    quantity_in_stock: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def profit_per_unit(self) -> Decimal:
        return self.selling_price - self.cost_price
