"""remvoe photos cols from trusted_agent_order table

Revision ID: 0dd0be3c7256
Revises: c51a29b96a0e
Create Date: 2024-07-28 00:42:05.039539

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0dd0be3c7256"
down_revision: Union[str, None] = "c51a29b96a0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
