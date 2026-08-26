from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models.product import Product
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleResponse

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Row-level lock so concurrent sales against the same product can't both
    # pass the stock check against a stale quantity_in_stock.
    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.business_id == current_user.business_id)
        .with_for_update()
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.quantity > product.quantity_in_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.quantity_in_stock} in stock",
        )

    sale = Sale(
        business_id=current_user.business_id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_cost_price=product.cost_price,
        unit_selling_price=product.selling_price,
        sold_at=payload.sold_at or datetime.now(timezone.utc),
    )
    product.quantity_in_stock -= payload.quantity

    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.get("", response_model=list[SaleResponse])
def list_sales(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Sale)
        .options(joinedload(Sale.product))
        .filter(Sale.business_id == current_user.business_id)
    )
    if date_from:
        query = query.filter(Sale.sold_at >= date_from)
    if date_to:
        query = query.filter(Sale.sold_at <= date_to)
    return query.order_by(Sale.sold_at.desc()).all()
