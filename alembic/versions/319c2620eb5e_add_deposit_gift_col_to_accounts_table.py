"""add deposit_gift col to accounts table

Revision ID: 319c2620eb5e
Revises: 9f5c9de8cbf8
Create Date: 2024-09-22 20:10:43.771727

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "319c2620eb5e"
down_revision: Union[str, None] = "9f5c9de8cbf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.add_column(sa.Column(name="deposit_gift", type_=sa.Float))


def downgrade() -> None:
    pass
