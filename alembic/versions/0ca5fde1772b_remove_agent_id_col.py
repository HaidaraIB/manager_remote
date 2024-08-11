"""remove agent_id col

Revision ID: 0ca5fde1772b
Revises: 910529e7a01f
Create Date: 2024-08-11 17:52:51.592428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ca5fde1772b'
down_revision: Union[str, None] = '910529e7a01f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.drop_column("agent_id")
    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.drop_column("agent_id")

def downgrade() -> None:
    pass
