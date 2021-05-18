"""drop_if_exists_User_canBookFreeOffers

Revision ID: 97553c40978d
Revises: 2c062a40154e
Create Date: 2021-05-18 07:44:00.970324

"""
from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = "97553c40978d"
down_revision = "2c062a40154e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        text(
            """
        ALTER TABLE "user"
        DROP COLUMN IF EXISTS "canBookFreeOffers"
        """
        )
    )


def downgrade():
    pass
