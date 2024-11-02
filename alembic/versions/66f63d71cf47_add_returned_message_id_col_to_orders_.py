"""add returned_message_id col to orders tables

Revision ID: 66f63d71cf47
Revises: 269519fe883b
Create Date: 2024-08-26 15:27:53.193193

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "66f63d71cf47"
down_revision: Union[str, None] = "269519fe883b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("deposit_orders") as batch_op:
            batch_op.add_column(
                sa.Column(name="returned_message_id", type_=sa.Integer, default=0)
            )

        with op.batch_alter_table("withdraw_orders") as batch_op:
            batch_op.add_column(
                sa.Column(name="returned_message_id", type_=sa.Integer, default=0)
            )

        with op.batch_alter_table("busdt_orders") as batch_op:
            batch_op.add_column(
                sa.Column(name="returned_message_id", type_=sa.Integer, default=0)
            )
    except:
        pass


def downgrade() -> None:
    pass
