"""Migrate visible brand fields and owned resource URLs without renaming jobs."""
from alembic import op

revision = 'modelone_brand_20260921'
down_revision = '40e1215ccbd6'
branch_labels = None
depends_on = None

def upgrade():
    from myapp.brand import BRAND, resolve_resources
    from myapp.brand_migration import migrate_connection
    # Introspection skips genuinely absent modules; SQL errors must abort upgrade.
    migrate_connection(op.get_bind(), BRAND, resolve_resources)

def downgrade():
    raise RuntimeError('Brand text cannot be reconstructed. Restore the pre-upgrade database backup.')
