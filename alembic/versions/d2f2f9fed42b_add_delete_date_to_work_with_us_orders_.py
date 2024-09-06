"""add delete date to work_with_us_orders table

Revision ID: d2f2f9fed42b
Revises: a798812b6e1b
Create Date: 2024-09-06 15:05:34.988836

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2f2f9fed42b"
down_revision: Union[str, None] = "a798812b6e1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("work_with_us_orders") as batch_op:
        batch_op.add_column(
            sa.Column(
                name="delete_date",
                type_=sa.TIMESTAMP,
            )
        )


def downgrade() -> None:
    pass
