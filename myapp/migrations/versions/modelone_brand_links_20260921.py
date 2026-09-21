"""Cover image documentation, preview assets and dataset source descriptions."""
from alembic import op

revision = 'modelone_brand_links_20260921'
down_revision = 'modelone_brand_20260921'
branch_labels = None
depends_on = None


def upgrade():
    from myapp.brand import BRAND, resolve_resources
    from myapp.brand_migration import migrate_connection
    # Existing brand-baseline installations also receive the expanded field set.
    migrate_connection(op.get_bind(), BRAND, resolve_resources)


def downgrade():
    raise RuntimeError('Restore the pre-upgrade database backup to recover original brand content.')
