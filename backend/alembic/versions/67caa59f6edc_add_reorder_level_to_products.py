"""add reorder level to products

Revision ID: 67caa59f6edc
Revises: 13602b1facbe
Create Date: 2026-09-03 19:07:07.382825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67caa59f6edc'
down_revision: Union[str, None] = '13602b1facbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("products", "reorder_level", server_default=None)


def downgrade() -> None:
    op.drop_column("products", "reorder_level")
