"""remvoe photos cols from trusted_agent_order table

Revision ID: 28587084bd41
Revises: 7f883fea2409
Create Date: 2024-08-02 21:59:29.042808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28587084bd41'
down_revision: Union[str, None] = '7f883fea2409'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("trusted_agents_orders") as batch_op:
            batch_op.drop_column("front_id")
            batch_op.drop_column("front_unique_id")
            batch_op.drop_column("front_width")
            batch_op.drop_column("front_height")
            batch_op.drop_column("front_size")

            batch_op.drop_column("back_id")
            batch_op.drop_column("back_unique_id")
            batch_op.drop_column("back_width")
            batch_op.drop_column("back_height")
            batch_op.drop_column("back_size")
    except:
        pass


def downgrade() -> None:
    pass
