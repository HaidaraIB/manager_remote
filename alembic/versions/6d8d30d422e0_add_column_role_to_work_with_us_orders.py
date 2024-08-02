"""add column role to work_with_us_orders

Revision ID: 6d8d30d422e0
Revises: a196f9267240
Create Date: 2024-08-02 23:44:36.356516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d8d30d422e0'
down_revision: Union[str, None] = 'a196f9267240'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("work_with_us_orders") as batch_op:
        batch_op.add_column(sa.Column("role", sa.Text))



def downgrade() -> None:
    pass
