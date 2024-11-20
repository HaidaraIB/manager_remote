"""add offer col to orders tables

Revision ID: 8f35af243056
Revises: 20e88fbdfeb5
Create Date: 2024-11-18 11:50:26.694580

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f35af243056"
down_revision: Union[str, None] = "20e88fbdfeb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("withdraw_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="offer",
                    type_=sa.Float,
                    default=0,
                )
            )
        with op.batch_alter_table("busdt_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="offer",
                    type_=sa.Float,
                    default=0,
                )
            )
        with op.batch_alter_table("deposit_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="offer",
                    type_=sa.Float,
                    default=0,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
