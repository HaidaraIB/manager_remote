"""rename TrustedAgentsOrder.creation_date to order_date

Revision ID: 76308d1c895c
Revises: 437a0e34276d
Create Date: 2024-07-26 10:39:31.757100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76308d1c895c'
down_revision: Union[str, None] = '437a0e34276d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("trusted_agents_orders") as batch_op:
        batch_op.alter_column(
            column_name="creation_date",
            new_column_name="order_date"
        )



def downgrade() -> None:
    pass
