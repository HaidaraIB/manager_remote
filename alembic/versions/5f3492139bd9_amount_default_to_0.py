"""amount default to 0

Revision ID: 5f3492139bd9
Revises: 0fcb82a63e9d
Create Date: 2024-07-19 21:34:18.242539

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f3492139bd9"
down_revision: Union[str, None] = "0fcb82a63e9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.alter_column(
            "amount",
            type_=sa.Float,
            server_default='0',
        )
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.alter_column(
            "amount",
            type_=sa.Float,
            server_default='0',
        )
    with op.batch_alter_table("buy_usdt_orders") as batch_op:
        batch_op.alter_column(
            "amount",
            type_=sa.Float,
            server_default='0',
        )


def downgrade() -> None:
    pass
