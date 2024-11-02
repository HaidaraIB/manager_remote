"""add gov col to withdraw_orders table

Revision ID: 269519fe883b
Revises: 28e673b7e74a
Create Date: 2024-08-23 17:13:05.266077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '269519fe883b'
down_revision: Union[str, None] = '28e673b7e74a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("withdraw_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="gov",
                    type_=sa.String
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
