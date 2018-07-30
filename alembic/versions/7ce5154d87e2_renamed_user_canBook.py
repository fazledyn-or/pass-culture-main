"""empty message

Revision ID: 7ce5154d87e2
Revises: 11d603462200
Create Date: 2018-07-30 12:17:55.225619

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ce5154d87e2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', )
    op.alter_column('user', 'canBook', new_column_name='canBookFreeOffers')
    op.create_check_constraint(name='check_admin_cannot_book_free_offers',
                               table_name='user',
                               condition='("canBookFreeOffers" IS FALSE AND "isAdmin" IS TRUE)'
                                     + 'OR ("isAdmin" IS FALSE)'
                               )


def downgrade():
    pass
