"""delete_enable_csv_multi_download_button_ff
"""


# pre/post deployment: post
# revision identifiers, used by Alembic.
revision = "93551ad5b84c"
down_revision = "f94795ee981a"
branch_labels = None
depends_on = None


def get_flag():
    # Do not import `pcapi.models.feature` at module-level. It breaks
    # `alembic history` with a SQLAlchemy error that complains about
    # an unknown table name while initializing the ORM mapper.
    from pcapi.models import feature

    return feature.Feature(
        name="ENABLE_CSV_MULTI_DOWNLOAD_BUTTON",
        isActive=False,
        description="Active le multi-téléchargement des réservations",
    )


def upgrade() -> None:
    from pcapi.models import feature

    feature.remove_feature_from_database(get_flag())


def downgrade() -> None:
    from pcapi.models import feature

    feature.add_feature_to_database(get_flag())
