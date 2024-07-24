"""drop column archive_message_ids

Revision ID: 437a0e34276d
Revises: 3f2cbcdbacb9
Create Date: 2024-07-24 22:24:56.463650

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "437a0e34276d"
down_revision: Union[str, None] = "3f2cbcdbacb9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.drop_column("archive_message_ids")
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.drop_column("archive_message_ids")
    with op.batch_alter_table("buy_usdt_orders") as batch_op:
        batch_op.drop_column("archive_message_ids")


def downgrade() -> None:
    pass
