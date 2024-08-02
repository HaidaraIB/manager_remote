"""add column agent id to deposit and withdraw tables

Revision ID: 7f883fea2409
Revises: ddf7cd18d464
Create Date: 2024-08-02 21:57:31.149687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f883fea2409'
down_revision: Union[str, None] = 'ddf7cd18d464'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("deposit_orders") as batch_op:
            batch_op.add_column(sa.Column(name="agent_id", type_=sa.Integer, default=0))
        with op.batch_alter_table("withdraw_orders") as batch_op:
            batch_op.add_column(sa.Column(name="agent_id", type_=sa.Integer, default=0))
    except:
        pass

def downgrade() -> None:
    pass
