"""rename ghafla_offers to offers

Revision ID: 8b88c5c71936
Revises: a658d0d673ec
Create Date: 2024-11-11 02:03:43.133481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b88c5c71936'
down_revision: Union[str, None] = 'a658d0d673ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.rename_table(old_table_name="ghafla_offers", new_table_name="offers")
    except:
        pass


def downgrade() -> None:
    try:
        op.rename_table(old_table_name="offers", new_table_name="ghafla_offers")
    except:
        pass
