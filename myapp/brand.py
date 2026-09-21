"""Single brand source: JSON defaults, then deployment environment overrides."""
import json
import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

CONFIG_PATH = Path(os.environ.get('MODELONE_CONFIG', Path(__file__).resolve().parents[1] / 'config/modelone.json'))
COLOR = re.compile(r'^#[0-9a-fA-F]{3,8}$')
FONT_FAMILY = re.compile(r'^[\w\s,._\-\"\']{1,200}$', re.UNICODE)
FIELDS = {
    'name': 'name', 'internal_name': 'internalName', 'title': 'title',
    'description': 'description', 'copyright_holder': 'copyrightHolder',
    'copyright_year': 'copyrightYear', 'support_url': 'supportUrl',
    'help_url': 'helpUrl', 'terms_url': 'termsUrl', 'privacy_url': 'privacyUrl',
    'image_registry': 'imageRegistry', 'asset_base_url': 'assetBaseUrl',
    'deployment_name': 'deploymentName', 'logo_url': 'logoUrl',
    'logo_reverse_url': 'logoReverseUrl', 'favicon_url': 'faviconUrl',
    'primary_color': 'primaryColor', 'font_family': 'fontFamily',
}

def load_brand():
    with CONFIG_PATH.open(encoding='utf-8') as source:
        config = json.load(source)
    brand = {key: os.environ.get('MODELONE_' + key.upper(), config.get(field, '')) for key, field in FIELDS.items()}
    for key in ('help_url', 'support_url', 'terms_url', 'privacy_url', 'logo_url', 'logo_reverse_url', 'favicon_url', 'asset_base_url'):
        value = brand[key]
        if value and (not value.startswith(('https://', 'http://', '/')) or value.startswith('//') or any(c in value for c in ('\"', "'", '<', '>', '\n', '\r'))):
            raise ValueError('Invalid brand URL: ' + key)
    if brand['primary_color'] and not COLOR.fullmatch(brand['primary_color']):
        raise ValueError('primary_color must be a hexadecimal CSS color')
    if brand['font_family'] and not FONT_FAMILY.fullmatch(brand['font_family']):
        raise ValueError('font_family contains unsupported CSS characters')
    brand['copyright_year'] = brand['copyright_year'] or str(date.today().year)
    brand['copyright'] = ('Copyright © %s %s. All Rights Reserved.' % (brand['copyright_year'], brand['copyright_holder'])) if brand['copyright_holder'] else ''
    return brand

BRAND = load_brand()


def validate_release_settings(include_links=True):
    required = ['image_registry', 'asset_base_url']
    if include_links:
        required += ['copyright_holder', 'help_url', 'support_url', 'terms_url', 'privacy_url']
    missing = [key for key in required if not BRAND[key].strip()]
    if missing:
        raise ValueError('Missing enterprise settings: ' + ', '.join(missing))
    registry = BRAND['image_registry'].rstrip('/')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*(?::[0-9]{1,5})?(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*', registry):
        raise ValueError('image_registry must be a registry host/path without scheme or credentials')
    if registry.endswith('/modelone'):
        raise ValueError('image_registry must not include the modelone namespace')
    for key in [key for key in required if key.endswith('_url')]:
        value = BRAND[key]
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username
                or parsed.password or any(c.isspace() for c in value)
                or re.search(r'cube[-_]?studio|data-master\.net|github\.com/data-infra', value, re.I)):
            raise ValueError(key + ' must be a full enterprise HTTP(S) URL without credentials')
        if key == 'asset_base_url' and (parsed.query or parsed.fragment):
            raise ValueError('asset_base_url must not contain a query or fragment')
    if re.search(r'cube[-_]?studio|cube-argoproj', registry, re.I):
        raise ValueError('image_registry must use an enterprise-owned namespace')

# Source filenames remain in the migration inventory, while published media
# use the same filenames as the modelOne tutorial cards.
ASSET_ALIASES = {
    'cube-studio.mp4': 'tutorial-pipeline.mp4',
    'job-template.mp4': 'tutorial-job-template.mp4',
}

def asset_path(path):
    path = path.lstrip('/')
    return ASSET_ALIASES.get(path, path)

def public_brand():
    # Explicit allowlist: infrastructure settings never reach the browser.
    return {field: BRAND[key] for key, field in FIELDS.items() if key not in ('image_registry', 'asset_base_url', 'deployment_name')} | {'assetBaseUrl': BRAND['asset_base_url'], 'copyright': BRAND['copyright']}

def brand_asset(path):
    base = BRAND['asset_base_url'].rstrip('/') or '/static/assets/modelone'
    return base + '/' + asset_path(path)

def image_repository(path):
    base = BRAND['image_registry'].rstrip('/')
    return (base + '/' if base else '') + 'modelone/' + path.lstrip('/')


def download_filename(filename=None, extension=None):
    """Return a safe, product-branded filename for user downloads."""
    value = os.path.basename(str(filename or 'download').replace('\\', '/')).strip() or 'download'
    value = re.sub(r'cube[-_ ]?studio', 'modelone', value, flags=re.I)
    value = (value.replace('开源版', '当前版本').replace('商业版', '当前版本')
                  .replace('开源社区', '平台支持'))
    prefix = BRAND.get('internal_name') or 'modelone'
    if not re.match(r'^' + re.escape(prefix) + r'(?:[-_.]|$)', value, re.I):
        value = prefix + '-' + value
    if extension:
        suffix = '.' + str(extension).lstrip('.')
        if not value.lower().endswith(suffix.lower()):
            value += suffix
    return value


def resolve_field(key, value):
    if key in ('gitpath', 'help_url') and isinstance(value, str) and value.startswith(('/job-template/', '/images/')):
        return BRAND['help_url']
    return resolve_resources(value)

def resolve_resources(value):
    """Resolve only owned references; preserve API, mount and SDK identifiers."""
    if isinstance(value, dict):
        return {key: resolve_field(key, item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_resources(item) for item in value]
    if not isinstance(value, str):
        return value
    for prefix in ('https://cube-studio.oss-cn-hangzhou.aliyuncs.com/', 'http://cube-studio.oss-cn-hangzhou.aliyuncs.com/', '/static/assets/modelone/'):
        for old, new in ASSET_ALIASES.items():
            value = re.sub(re.escape(prefix + old) + r'(?=$|[?\s#\x22\x27<>\]\}),])', lambda _: prefix + new, value)
    value = re.sub(r'https?://cube-studio\.oss-cn-hangzhou\.aliyuncs\.com/', brand_asset(''), value)
    if value == 'ccr.ccs.tencentyun.com/cube-studio':
        return image_repository('').rstrip('/')
    value = value.replace('ccr.ccs.tencentyun.com/cube-studio/', image_repository(''))
    # A registry prefix already resolved above must not be prefixed twice.
    value = re.sub(r'(?<![\w/.-])modelone/(?=[A-Za-z0-9])', lambda _: image_repository(''), value)
    return re.sub(r'(?<![\w/.:])/static/assets/modelone/', lambda _: brand_asset(''), value)
