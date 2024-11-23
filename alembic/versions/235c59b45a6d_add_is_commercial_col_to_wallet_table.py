"""add is_commercial col to wallet table

Revision ID: 235c59b45a6d
Revises: fc01050bcad3
Create Date: 2024-11-23 23:33:35.321665

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "235c59b45a6d"
down_revision: Union[str, None] = "fc01050bcad3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("wallets") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="is_commercial",
                    type_=sa.Boolean,
                    server_default="0",
                    default=0,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
