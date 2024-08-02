"""add col agent_id to deposit and withdraw order tables

Revision ID: c51a29b96a0e
Revises: 76308d1c895c
Create Date: 2024-07-27 13:30:53.193798

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c51a29b96a0e"
down_revision: Union[str, None] = "76308d1c895c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.add_column(sa.Column(name="agent_id", type_=sa.Integer, default=0))
    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.add_column(sa.Column(name="agent_id", type_=sa.Integer, default=0))


def downgrade() -> None:
    pass
