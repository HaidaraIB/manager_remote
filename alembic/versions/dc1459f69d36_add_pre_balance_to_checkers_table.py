"""add pre_balance to checkers table

Revision ID: dc1459f69d36
Revises: 8e9e5ed86c50
Create Date: 2024-08-14 01:19:03.754504

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dc1459f69d36"
down_revision: Union[str, None] = "8e9e5ed86c50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("checkers") as batch_op:
        batch_op.add_column(
            sa.Column(
                name="pre_balance",
                type_=sa.Float,
                default=0,
            )
        )


def downgrade() -> None:
    pass
