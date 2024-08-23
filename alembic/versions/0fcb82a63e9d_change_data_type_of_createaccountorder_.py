"""change data type of CreateAccountOrder national_number

Revision ID: 0fcb82a63e9d
Revises: f5f4d6f4e373
Create Date: 2024-07-15 13:31:41.775030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fcb82a63e9d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
