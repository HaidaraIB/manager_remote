"""change PK constraint for checkers table

Revision ID: 2f740ae8caf3
Revises: 41be479906d0
Create Date: 2024-08-12 23:01:17.367197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f740ae8caf3'
down_revision: Union[str, None] = '41be479906d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
