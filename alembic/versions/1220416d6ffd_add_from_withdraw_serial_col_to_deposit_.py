"""add from_withdraw_serial col to deposit_orders table

Revision ID: 1220416d6ffd
Revises: dfa6ebb6d5c6
Create Date: 2024-10-26 15:33:55.408245

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1220416d6ffd"
down_revision: Union[str, None] = "dfa6ebb6d5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("withdraw_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="cancel_date",
                    type_=sa.TIMESTAMP,
                )
            )
            batch_op.add_column(
                sa.Column(
                    name="split_date",
                    type_=sa.TIMESTAMP,
                )
            )
            
        with op.batch_alter_table("deposit_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="from_withdraw_serial",
                    type_=sa.Integer,
                    default=0,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
