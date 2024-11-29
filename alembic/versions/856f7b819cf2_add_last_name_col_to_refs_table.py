"""add last_name col to refs table

Revision ID: 856f7b819cf2
Revises: 235c59b45a6d
Create Date: 2024-11-29 16:58:27.600380

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "856f7b819cf2"
down_revision: Union[str, None] = "235c59b45a6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("ref_numbers") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="last_name",
                    type_=sa.String,
                    server_default="",
                    default="",
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
