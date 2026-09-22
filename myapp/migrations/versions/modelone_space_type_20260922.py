"""Collapse team/resource rows into single-layer workspaces (type='space').

One idempotent rule: rows typed 'org', or untyped rows referenced by members
or business assets, become workspaces. The previous type is stamped into the
expand JSON so downgrade restores the exact pre-upgrade values.
"""
import json

from alembic import op
import sqlalchemy as sa

revision = 'modelone_space_type_20260922'
down_revision = 'modelone_brand_links_20260921'
branch_labels = None
depends_on = None

STAMP = '_mo_space_from'
# Rows with these types stay catalog entries, never workspaces.
CATALOG_TYPES = ('job-template', 'job_template', 'model')


def _referencing_tables(bind):
    inspector = sa.inspect(bind)
    tables = []
    for name in inspector.get_table_names():
        columns = [column['name'] for column in inspector.get_columns(name)]
        if 'project_id' in columns and name != 'project':
            tables.append(name)
    return tables


def _expand_dict(expand):
    try:
        data = json.loads(expand) if expand else {}
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def upgrade_tables(bind):
    """Apply the workspace type rewrite; returns the number of changed rows."""
    projects = bind.execute(sa.text('SELECT id, type, expand FROM project')).fetchall()
    referenced = set()
    for table in _referencing_tables(bind):
        rows = bind.execute(sa.text(
            'SELECT DISTINCT project_id FROM %s WHERE project_id IS NOT NULL' % table))
        referenced.update(row[0] for row in rows)
    changed = 0
    for project_id, project_type, expand in projects:
        if project_type == 'space' or project_type in CATALOG_TYPES:
            continue
        if project_type != 'org' and project_id not in referenced:
            continue
        data = _expand_dict(expand)
        data[STAMP] = project_type or ''
        bind.execute(
            sa.text('UPDATE project SET type = :type, expand = :expand WHERE id = :id'),
            {'type': 'space', 'expand': json.dumps(data, ensure_ascii=False), 'id': project_id},
        )
        changed += 1
    return changed


def downgrade_tables(bind):
    """Restore stamped rows to their pre-upgrade type; returns changed rows."""
    projects = bind.execute(sa.text('SELECT id, type, expand FROM project')).fetchall()
    changed = 0
    for project_id, project_type, expand in projects:
        if project_type != 'space':
            continue
        data = _expand_dict(expand)
        if STAMP not in data:
            continue
        original = data.pop(STAMP)
        bind.execute(
            sa.text('UPDATE project SET type = :type, expand = :expand WHERE id = :id'),
            {'type': original or None, 'expand': json.dumps(data, ensure_ascii=False), 'id': project_id},
        )
        changed += 1
    return changed


def upgrade():
    upgrade_tables(op.get_bind())


def downgrade():
    downgrade_tables(op.get_bind())
