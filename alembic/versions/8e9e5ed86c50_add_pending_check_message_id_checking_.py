"""add pending_check_message_id, checking_message_id back to deposit_orders table

Revision ID: 8e9e5ed86c50
Revises: 2f740ae8caf3
Create Date: 2024-08-12 23:21:02.189733

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e9e5ed86c50"
down_revision: Union[str, None] = "2f740ae8caf3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
