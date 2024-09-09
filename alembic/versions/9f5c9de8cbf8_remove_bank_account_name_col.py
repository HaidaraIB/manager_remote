"""remove bank_account_name col

Revision ID: 9f5c9de8cbf8
Revises: d2f2f9fed42b
Create Date: 2024-09-09 14:44:13.856064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f5c9de8cbf8'
down_revision: Union[str, None] = 'd2f2f9fed42b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.drop_column("bank_account_name")
    with op.batch_alter_table("busdt_orders") as batch_op:
        batch_op.drop_column("bank_account_name")


def downgrade() -> None:
    pass
