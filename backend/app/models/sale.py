from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_sales_quantity_positive"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    business = relationship("Business", back_populates="sales")
    product = relationship("Product", back_populates="sales")

    @property
    def product_name(self) -> str:
        return self.product.name
