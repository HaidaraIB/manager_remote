"""busdt_orders related updates

Revision ID: a196f9267240
Revises: 0dd0be3c7256
Create Date: 2024-08-02 23:32:27.248941

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a196f9267240"
down_revision: Union[str, None] = "0dd0be3c7256"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("buy_usdt_orders", "busdt_orders")
    op.rename_table("trusted_agents_orders", "work_with_us_orders")
    with op.batch_alter_table("photos") as batch_op:
        batch_op.execute(
            """
                UPDATE photos SET order_type = 'busdt' WHERE order_type = 'buy_usdt';
            """
        )
    with op.batch_alter_table("checkers") as batch_op:
        batch_op.execute(
            """
                UPDATE checkers SET check_what = 'busdt' WHERE check_what = 'buy_usdt';
            """
        )


def downgrade() -> None:
    pass
