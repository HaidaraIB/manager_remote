"""add method to Checker

Revision ID: 41be479906d0
Revises: 532cda73890b
Create Date: 2024-08-12 19:22:42.029027

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "41be479906d0"
down_revision: Union[str, None] = "532cda73890b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
