"""add acc_from_bot col to deposit_orders table

Revision ID: fbfbd096025a
Revises: 0ca5fde1772b
Create Date: 2024-08-11 18:19:43.535772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbfbd096025a'
down_revision: Union[str, None] = '0ca5fde1772b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.add_column(
            column=sa.Column(
                name="acc_from_bot",
                type_=sa.Boolean,
            ),
        )


def downgrade() -> None:
    pass
