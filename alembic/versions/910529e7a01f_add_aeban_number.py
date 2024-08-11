"""add aeban number

Revision ID: 910529e7a01f
Revises: f75a643ca7fa
Create Date: 2024-08-11 17:19:06.514520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '910529e7a01f'
down_revision: Union[str, None] = 'f75a643ca7fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("busdt_orders") as batch_op:
        batch_op.add_column(
            column=sa.Column(
                name="aeban_number",
                type_=sa.String,
            ),
        )
    with op.batch_alter_table("withdraw_orders") as batch_op:
        batch_op.add_column(
            column=sa.Column(
                name="aeban_number",
                type_=sa.String,
            ),
        )


def downgrade() -> None:
    pass
