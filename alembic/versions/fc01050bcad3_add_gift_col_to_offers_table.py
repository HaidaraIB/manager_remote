"""add gift col to offers table

Revision ID: fc01050bcad3
Revises: 76f2f52fbce5
Create Date: 2024-11-21 13:41:44.399715

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fc01050bcad3"
down_revision: Union[str, None] = "76f2f52fbce5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("offers") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="gift",
                    type_=sa.Float,
                    server_default="0",
                    default=0,
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
