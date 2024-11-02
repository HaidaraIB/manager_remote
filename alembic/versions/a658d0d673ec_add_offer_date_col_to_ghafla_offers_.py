"""add offer_date col to ghafla_offers table

Revision ID: a658d0d673ec
Revises: 1220416d6ffd
Create Date: 2024-11-02 21:17:35.276576

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a658d0d673ec"
down_revision: Union[str, None] = "1220416d6ffd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("ghafla_offers") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="offer_date",
                    type_=sa.TIMESTAMP,
                    server_default=sa.func.current_timestamp(),
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
