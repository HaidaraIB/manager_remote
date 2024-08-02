"""rename buy_usdt_orders to busdt_orders

Revision ID: ddf7cd18d464
Revises: 
Create Date: 2024-08-02 20:57:45.488754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddf7cd18d464'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.rename_table("buy_usdt_orders", "busdt_orders")
    except:
        pass



def downgrade() -> None:
    pass
