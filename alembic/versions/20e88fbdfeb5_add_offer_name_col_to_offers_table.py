"""add offer_name col to offers table

Revision ID: 20e88fbdfeb5
Revises: 8b88c5c71936
Create Date: 2024-11-11 19:50:38.078980

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20e88fbdfeb5"
down_revision: Union[str, None] = "8b88c5c71936"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("offers") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="offer_name",
                    type_=sa.String,
                    server_default="عرض الغفلة",
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
