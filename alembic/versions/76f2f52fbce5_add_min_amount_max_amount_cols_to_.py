"""add min_amount max_amount cols to offers table

Revision ID: 76f2f52fbce5
Revises: 8f35af243056
Create Date: 2024-11-20 16:37:16.410829

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "76f2f52fbce5"
down_revision: Union[str, None] = "8f35af243056"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("offers") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="min_amount",
                    type_=sa.Float,
                    server_default='0',
                    default=0,
                )
            )
            batch_op.add_column(
                sa.Column(
                    name="max_amount",
                    type_=sa.Float,
                    server_default='0',
                    default=0,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
