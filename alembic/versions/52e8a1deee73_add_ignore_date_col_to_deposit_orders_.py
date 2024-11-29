"""add ignore_date col to deposit_orders table

Revision ID: 52e8a1deee73
Revises: 856f7b819cf2
Create Date: 2024-11-29 17:22:53.763791

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "52e8a1deee73"
down_revision: Union[str, None] = "856f7b819cf2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("deposit_orders") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="ignore_date",
                    type_=sa.TIMESTAMP,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
