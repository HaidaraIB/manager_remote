"""add gov col to deposit_orders table

Revision ID: 28e673b7e74a
Revises: dc1459f69d36
Create Date: 2024-08-17 22:01:31.580394

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "28e673b7e74a"
down_revision: Union[str, None] = "dc1459f69d36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
