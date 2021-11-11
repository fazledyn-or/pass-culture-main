"""migrate_id_at_provider_part_2

Revision ID: e8199ef92975
Revises: 20290f0b5d4f
Create Date: 2021-04-30 14:33:46.259861

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "e8199ef92975"
down_revision = "20290f0b5d4f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("COMMIT")
    op.execute('CREATE UNIQUE INDEX CONCURRENTLY "venueId_idAtProvider_index" ON offer ("venueId", "idAtProvider")')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("venueId_idAtProvider_index", table_name="offer")
    # ### end Alembic commands ###
