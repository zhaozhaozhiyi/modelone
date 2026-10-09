"""Create AIHub's versioned application catalog and request audit."""
from alembic import op
import sqlalchemy as sa


revision = 'aihub_portal_20261008'
down_revision = 'modelone_space_type_20260922'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'aihub_application_version',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(80), nullable=False),
        sa.Column('version', sa.String(40), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('summary', sa.String(2000), nullable=False),
        sa.Column('category', sa.String(40), nullable=False),
        sa.Column('task', sa.String(100), nullable=False),
        sa.Column('model_source', sa.String(500), nullable=False),
        sa.Column('license_name', sa.String(100), nullable=False),
        sa.Column('weight_digest', sa.String(200), nullable=False),
        sa.Column('visibility', sa.String(20), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.id'), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('ab_user.id'), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('input_schema', sa.Text(), nullable=False),
        sa.Column('output_schema', sa.Text(), nullable=False),
        sa.Column('endpoint_url', sa.String(500), nullable=False),
        sa.Column('endpoint_revision', sa.String(200), nullable=False),
        sa.Column('credential_env', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by_id', sa.Integer(), sa.ForeignKey('ab_user.id'), nullable=True),
        sa.UniqueConstraint('slug', 'version', name='uq_aihub_slug_version'),
    )
    op.create_index('ix_aihub_application_version_slug', 'aihub_application_version', ['slug'])
    op.create_table(
        'aihub_invocation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('version_id', sa.Integer(), sa.ForeignKey('aihub_application_version.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('ab_user.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_type', sa.String(60), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_aihub_invocation_version_id', 'aihub_invocation', ['version_id'])


def downgrade():
    op.drop_index('ix_aihub_invocation_version_id', table_name='aihub_invocation')
    op.drop_table('aihub_invocation')
    op.drop_index('ix_aihub_application_version_slug', table_name='aihub_application_version')
    op.drop_table('aihub_application_version')
