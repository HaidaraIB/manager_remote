"""add delete_date col to orders tables

Revision ID: a798812b6e1b
Revises: 66f63d71cf47
Create Date: 2024-08-26 16:23:08.393884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a798812b6e1b'
down_revision: Union[str, None] = '66f63d71cf47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.add_column(
            sa.Column(name="delete_date", type_=sa.TIMESTAMP)
        )

    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.add_column(
            sa.Column(name="delete_date", type_=sa.TIMESTAMP)
        )

    with op.batch_alter_table("busdt_orders") as batch_op:
        batch_op.add_column(
            sa.Column(name="delete_date", type_=sa.TIMESTAMP)
        )


def downgrade() -> None:
    pass
