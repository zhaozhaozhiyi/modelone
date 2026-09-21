"""Brand migration helpers. Identifiers, paths and third-party notices are preserved."""
import json
import re

LEGACY_HELP = re.compile(r'https?://(?:github\.com|githubfast\.com)/data-infra/cube-studio[^\s<>"\']*', re.I)
LEGACY_NAME = re.compile(r'(?<![A-Za-z0-9_/.:-])cube[- ]?studio(?![A-Za-z0-9_/.:-])', re.I)

# Do not rename `name` identifiers: API URLs, jobs and unique constraints use them.
DISPLAY_FIELDS = ('label', 'describe', 'description', 'hello', 'tips', 'prompt', 'doc', 'producer')
RESOURCE_FIELDS = ('images', 'image', 'download_url', 'url', 'path', 'model_path', 'pic', 'pre_train_model', 'knowledge', 'service_config', 'args', 'expand', 'dataset', 'notebook', 'job_template', 'pipeline', 'inference', 'service')
TABLES = ('project', 'dataset', 'images', 'job_template', 'pipeline', 'task', 'service', 'inferenceservice', 'notebook', 'aihub', 'chat', 'model', 'training_model', 'train_model', 'repository', 'metadata_table')

def rewrite(value, resolve_resources, help_url='', display=False):
    if value is None or not isinstance(value, str):
        return value
    # Deserialize before replacing URLs so quoted configuration stays valid.
    if value.lstrip().startswith(('{', '[')):
        try:
            parsed = json.loads(value)
        except ValueError:
            pass
        else:
            def walk(item):
                if isinstance(item, dict):
                    return {key: walk_display(val, key in DISPLAY_FIELDS) for key, val in item.items()}
                if isinstance(item, list):
                    return [walk(val) for val in item]
                return rewrite(item, resolve_resources, help_url, display)
            def walk_display(item, visible):
                if isinstance(item, (list, dict)):
                    return walk(item)
                return rewrite(item, resolve_resources, help_url, visible)
            updated = walk(parsed)
            return value if updated == parsed else json.dumps(updated, ensure_ascii=False)
    value = re.sub(r'<a\b[^>]*href=["\']https?://(?:github\.com|githubfast\.com)/data-infra/cube-studio[^>]*>.*?</a>', '帮助中心' if help_url else '', value, flags=re.I | re.S)
    value = resolve_resources(value)
    value = LEGACY_HELP.sub(lambda _: help_url, value)
    # Only the known example knowledge file moves; general mount paths stay intact.
    value = value.replace('/pipeline/example/gpt/cube-studio.csv', '/pipeline/example/gpt/modelone.csv')
    if display:
        value = LEGACY_NAME.sub('modelOne', value)
        value = value.replace('开源社区', '平台支持').replace('开源版本', '当前版本').replace('商业版本', '当前版本').replace('开源版', '当前版本').replace('商业版', '当前版本')
    return value

def migrate_connection(bind, brand, resolve_resources):
    import sqlalchemy as sa
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    changed = 0
    for name in TABLES:
        if name not in existing:
            continue
        table = sa.Table(name, sa.MetaData(), autoload_with=bind)
        keys = list(table.primary_key.columns)
        if not keys:
            continue
        names = [field for field in DISPLAY_FIELDS + RESOURCE_FIELDS if field in table.c and isinstance(table.c[field].type, (sa.String, sa.Text))]
        if name == 'metadata_table' and 'app' in table.c:
            names.append('app')
        if name == 'repository' and 'server' in table.c:
            names.append('server')
        if name == 'images' and 'name' in table.c:
            names.append('name')  # An image reference, not a job identity.
        names = list(dict.fromkeys(names))
        for row in bind.execute(sa.select(table)).mappings().all():
            updates = {}
            for field in names:
                value = rewrite(row[field], resolve_resources, brand.get('help_url', ''), field in DISPLAY_FIELDS or (name == 'metadata_table' and field == 'app'))
                # Preserve serialized JSON validity and untouched technical fields.
                if isinstance(row[field], str) and row[field].lstrip().startswith(('{','[')):
                    try:
                        json.loads(row[field])
                    except ValueError:
                        pass
                    else:
                        json.loads(value)
                if value != row[field]:
                    updates[field] = value
            if name == 'chat' and row.get('name') == 'cube-studio' and 'icon' in table.c:
                from pathlib import Path
                icon = (Path(__file__).parent / 'static/assets/modelone/modelone-mark.svg').read_text(encoding='utf-8')
                if row['icon'] != icon:
                    updates['icon'] = icon
            if updates:
                where = sa.and_(*(key == row[key.name] for key in keys))
                bind.execute(table.update().where(where).values(**updates))
                changed += 1
    return changed
