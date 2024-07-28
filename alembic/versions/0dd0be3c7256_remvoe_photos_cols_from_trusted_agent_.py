"""remvoe photos cols from trusted_agent_order table

Revision ID: 0dd0be3c7256
Revises: c51a29b96a0e
Create Date: 2024-07-28 00:42:05.039539

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0dd0be3c7256"
down_revision: Union[str, None] = "c51a29b96a0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    pass
