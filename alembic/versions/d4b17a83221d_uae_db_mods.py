"""uae db mods

Revision ID: d4b17a83221d
Revises: 0dd0be3c7256
Create Date: 2024-07-28 21:40:28.950933

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4b17a83221d"
down_revision: Union[str, None] = "0dd0be3c7256"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.add_column(
            sa.Column(
                name="checking_message_id",
                type_=sa.Integer,
                default=0,
            )
        )
        batch_op.add_column(
            sa.Column(
                name="panding_check_message_id",
                type_=sa.Integer,
                default=0,
            )
        )


def downgrade() -> None:
    pass
