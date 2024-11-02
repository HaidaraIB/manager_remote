"""add procces_on_off cols to payment_methods table

Revision ID: dfa6ebb6d5c6
Revises: f42377fe0594
Create Date: 2024-09-28 13:36:02.287627

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dfa6ebb6d5c6"
down_revision: Union[str, None] = "f42377fe0594"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("payment_methods") as batch_op:
            batch_op.alter_column(
                column_name="on_off",
                new_column_name="deposit_on_off",
                type_=sa.Boolean,
            )
            batch_op.add_column(
                sa.Column(
                    name="withdraw_on_off",
                    type_=sa.Boolean,
                    default=1,
                )
            )
            batch_op.add_column(
                sa.Column(
                    name="busdt_on_off",
                    type_=sa.Boolean,
                    default=1,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
