"""add connection_to_user_date col to accounts table

Revision ID: f42377fe0594
Revises: 17fdbbef3cc5
Create Date: 2024-09-23 14:29:11.163293

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f42377fe0594"
down_revision: Union[str, None] = "17fdbbef3cc5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("accounts") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="connect_to_user_date",
                    type_=sa.TIMESTAMP,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
