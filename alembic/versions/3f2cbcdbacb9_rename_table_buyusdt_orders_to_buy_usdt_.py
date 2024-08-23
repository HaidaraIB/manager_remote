"""rename table buyusdt_orders to buy_usdt_orders

Revision ID: 3f2cbcdbacb9
Revises: 0833d9f9a249
Create Date: 2024-07-24 00:20:43.180181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f2cbcdbacb9'
down_revision: Union[str, None] = '0833d9f9a249'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
