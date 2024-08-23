"""busdt_orders related updates

Revision ID: a196f9267240
Revises: 0dd0be3c7256
Create Date: 2024-08-02 23:32:27.248941

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a196f9267240"
down_revision: Union[str, None] = "0dd0be3c7256"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
