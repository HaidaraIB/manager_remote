"""add neighborhood to TrustedAgent

Revision ID: 0833d9f9a249
Revises: 5f3492139bd9
Create Date: 2024-07-20 20:09:46.363011

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0833d9f9a249"
down_revision: Union[str, None] = "5f3492139bd9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("trusted_agents") as batch_op:
        batch_op.add_column(
            column=sa.Column(
                name="neighborhood",
                type_=sa.String,
            ),
        )


def downgrade() -> None:
    pass
