"""add complaint_date col to Complaint table

Revision ID: 17fdbbef3cc5
Revises: 319c2620eb5e
Create Date: 2024-09-23 12:45:18.466114

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "17fdbbef3cc5"
down_revision: Union[str, None] = "319c2620eb5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.batch_alter_table("complaints") as batch_op:
            batch_op.add_column(
                sa.Column(
                    name="complaint_date",
                    type_=sa.TIMESTAMP,
                    server_default=sa.func.current_timestamp(),
                )
            )
    except:
        pass


def downgrade() -> None:
    pass
