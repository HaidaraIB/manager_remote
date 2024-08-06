"""add deposit_wallet col to deposit_orders table

Revision ID: f75a643ca7fa
Create Date: 2024-08-06 21:29:53.346175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f75a643ca7fa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_orders") as batch_op:
        batch_op.add_column(
            column=sa.Column(
                name="deposit_wallet",
                type_=sa.String,
            ),
        )



def downgrade() -> None:
    pass
