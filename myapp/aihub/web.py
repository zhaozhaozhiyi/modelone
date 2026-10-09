"""Standalone AIHub page and versioned catalog API."""
import json
import time
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, redirect, request, send_from_directory
from flask_wtf.csrf import generate_csrf, validate_csrf
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from wtforms.validators import ValidationError

from myapp import db
from myapp.models.model_team import Project, Project_User
from .models import ApplicationVersion, Invocation
from .protocol import (CATEGORIES, HubError, predict, validate_application,
                       validate_endpoint_destination, validate_inputs, verify_endpoint)


FRONTEND = Path(__file__).resolve().parent / 'frontend'
blueprint = Blueprint('aihub_portal', __name__, url_prefix='/aihub',
                      static_folder=str(FRONTEND), static_url_path='/assets')


@blueprint.before_request
def require_login():
    if request.path.startswith('/aihub/assets/'):
        return
    user = getattr(g, 'user', None)
    if not user or not user.get_id() or not user.is_active:
        if request.path.startswith('/aihub/api/'):
            return jsonify(error={'code': 'unauthorized', 'message': '请先登录'}), 401
        return redirect('/login/')
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and not request.headers.get('Authorization'):
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except ValidationError:
            return jsonify(error={'code': 'csrf_invalid', 'message': '页面会话已失效，请刷新重试'}), 403


@blueprint.after_request
def no_store(response):
    if request.path.startswith('/aihub/api/') or request.path == '/aihub/':
        response.headers['Cache-Control'] = 'no-store'
    return response


@blueprint.errorhandler(HubError)
def handle_hub_error(error):
    return jsonify(error={'code': error.code, 'message': str(error)}), error.status


def admin_only():
    if not g.user.is_admin():
        raise HubError('只有平台管理员可以管理应用', 403, 'forbidden')


def allowed_hosts():
    configured = current_app.config.get('AIHUB_ENDPOINT_HOSTS', ())
    if isinstance(configured, str):
        configured = configured.split(',')
    return tuple(host.strip().lower() for host in configured if isinstance(host, str) and host.strip())


def visible(query):
    if g.user.is_admin():
        return query
    projects = db.session.query(Project_User.project_id).filter(Project_User.user_id == g.user.id)
    return query.filter(or_(
        ApplicationVersion.visibility == 'public',
        and_(ApplicationVersion.visibility == 'private', ApplicationVersion.owner_id == g.user.id),
        and_(ApplicationVersion.visibility == 'project', ApplicationVersion.project_id.in_(projects)),
    ))


def serialize(version, private=False):
    data = {
        'id': version.id,
        'slug': version.slug,
        'version': version.version,
        'name': version.name,
        'summary': version.summary,
        'category': version.category,
        'task': version.task,
        'model_source': version.model_source,
        'license_name': version.license_name,
        'weight_digest': version.weight_digest,
        'visibility': version.visibility,
        'state': version.state,
        'input_schema': json.loads(version.input_schema),
        'output_schema': json.loads(version.output_schema),
        'published_at': version.published_at.isoformat() + 'Z' if version.published_at else None,
    }
    if private:
        data.update(project_id=version.project_id, owner_id=version.owner_id,
                    endpoint_url=version.endpoint_url, endpoint_revision=version.endpoint_revision,
                    credential_env=version.credential_env)
    return data


def published(slug, version=None):
    query = visible(db.session.query(ApplicationVersion)).filter_by(slug=slug, state='published')
    if version:
        query = query.filter_by(version=version)
    record = query.order_by(ApplicationVersion.published_at.desc(), ApplicationVersion.id.desc()).first()
    if not record:
        raise HubError('应用不存在或无权访问', 404, 'not_found')
    return record


def form_payload():
    if request.content_length is not None and request.content_length > 1024 * 1024:
        raise HubError('请求不能超过 1 MiB', 413, 'too_large')
    if not request.is_json:
        raise HubError('请使用 application/json')
    raw = request.stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise HubError('请求不能超过 1 MiB', 413, 'too_large')
    try:
        return json.loads(raw)
    except (UnicodeError, ValueError):
        raise HubError('JSON 格式无效') from None


@blueprint.get('/')
def index():
    response = send_from_directory(FRONTEND, 'index.html')
    response.headers['Cache-Control'] = 'no-store'
    return response


@blueprint.get('/api/session')
def session_info():
    return jsonify(data={'username': g.user.username, 'is_admin': g.user.is_admin(),
                         'csrf_token': generate_csrf()})


@blueprint.get('/api/apps')
def catalog():
    category = request.args.get('category', '')
    search = request.args.get('q', '').strip()
    if category and category not in CATEGORIES:
        raise HubError('分类无效')
    if len(search) > 100:
        raise HubError('搜索词过长')
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        raise HubError('页码无效') from None
    if page < 1:
        raise HubError('页码无效')
    query = visible(db.session.query(ApplicationVersion)).filter_by(state='published')
    if category:
        query = query.filter_by(category=category)
    if search:
        term = '%' + search.replace('%', r'\%').replace('_', r'\_') + '%'
        query = query.filter(or_(ApplicationVersion.name.ilike(term, escape='\\'),
                                 ApplicationVersion.summary.ilike(term, escape='\\'),
                                 ApplicationVersion.task.ilike(term, escape='\\')))
    rows = query.order_by(ApplicationVersion.published_at.desc(), ApplicationVersion.id.desc()).all()
    latest = []
    seen = set()
    for row in rows:
        if row.slug not in seen:
            latest.append(row)
            seen.add(row.slug)
    size = 24
    return jsonify(data={'items': [serialize(row) for row in latest[(page - 1) * size:page * size]],
                         'total': len(latest), 'page': page, 'page_size': size,
                         'categories': list(CATEGORIES)})


@blueprint.get('/api/apps/<slug>')
def detail(slug):
    row = published(slug)
    versions = visible(db.session.query(ApplicationVersion)).filter_by(slug=slug, state='published') \
        .order_by(ApplicationVersion.published_at.desc()).all()
    return jsonify(data={'application': serialize(row), 'versions': [serialize(item) for item in versions]})


@blueprint.get('/api/apps/<slug>/versions/<version>')
def version_detail(slug, version):
    return jsonify(data=serialize(published(slug, version)))


@blueprint.get('/api/apps/<slug>/versions/<version>/health')
def health(slug, version):
    row = published(slug, version)
    try:
        verify_endpoint(row, allowed_hosts(), check_health=True)
        return jsonify(data={'status': 'healthy'})
    except HubError as error:
        return jsonify(data={'status': 'unavailable', 'reason': str(error)}), 200


@blueprint.post('/api/apps/<slug>/versions/<version>/predict')
def invoke(slug, version):
    row = published(slug, version)
    payload = form_payload()
    if not isinstance(payload, dict) or set(payload) != {'inputs'}:
        raise HubError('请求体必须包含 inputs 对象')
    validate_inputs(json.loads(row.input_schema), payload['inputs'])
    started = time.monotonic()
    error = None
    try:
        verify_endpoint(row, allowed_hosts(), check_health=True)
        result = predict(row, payload['inputs'], allowed_hosts())
        return jsonify(data={'result': result, 'version': row.version})
    except HubError as exc:
        error = exc
        raise
    finally:
        db.session.add(Invocation(version_id=row.id, user_id=g.user.id,
                                  status='failed' if error else 'success',
                                  error_type=error.code if error else '',
                                  duration_ms=int((time.monotonic() - started) * 1000)))
        db.session.commit()


@blueprint.get('/api/admin/apps')
def admin_catalog():
    admin_only()
    rows = db.session.query(ApplicationVersion).order_by(ApplicationVersion.created_at.desc(),
                                                         ApplicationVersion.id.desc()).limit(200).all()
    return jsonify(data={'items': [serialize(row, private=True) for row in rows]})


def assign(row, values):
    for key, value in values.items():
        setattr(row, key, json.dumps(value, ensure_ascii=False) if key.endswith('_schema') else value)


def check_project(values):
    if values['project_id'] is not None and not db.session.query(Project.id).filter_by(
            id=values['project_id']).filter(Project.type.in_(('space', 'org'))).first():
        raise HubError('指定的项目空间不存在')


def check_endpoint(values):
    validate_endpoint_destination(values['endpoint_url'], allowed_hosts())


@blueprint.post('/api/admin/apps')
def create_draft():
    admin_only()
    values = validate_application(form_payload())
    check_project(values)
    check_endpoint(values)
    row = ApplicationVersion(owner_id=g.user.id, state='draft', created_at=datetime.utcnow())
    assign(row, values)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise HubError('该应用版本已存在', 409, 'duplicate_version') from None
    return jsonify(data=serialize(row, private=True)), 201


@blueprint.put('/api/admin/apps/<int:record_id>')
def update_draft(record_id):
    admin_only()
    row = db.session.get(ApplicationVersion, record_id)
    if not row:
        raise HubError('应用版本不存在', 404, 'not_found')
    if row.state != 'draft':
        raise HubError('已发布版本不能修改', 409, 'immutable_version')
    values = validate_application(form_payload())
    check_project(values)
    check_endpoint(values)
    assign(row, values)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise HubError('该应用版本已存在', 409, 'duplicate_version') from None
    return jsonify(data=serialize(row, private=True))


@blueprint.post('/api/admin/apps/<int:record_id>/publish')
def publish(record_id):
    admin_only()
    row = db.session.get(ApplicationVersion, record_id)
    if not row:
        raise HubError('应用版本不存在', 404, 'not_found')
    if row.state != 'draft':
        raise HubError('只有草稿可以发布', 409, 'invalid_state')
    verify_endpoint(row, allowed_hosts(), check_health=True)
    row.state = 'published'
    row.published_at = datetime.utcnow()
    row.published_by_id = g.user.id
    db.session.commit()
    return jsonify(data=serialize(row, private=True))


@blueprint.post('/api/admin/apps/<int:record_id>/retire')
def retire(record_id):
    admin_only()
    row = db.session.get(ApplicationVersion, record_id)
    if not row:
        raise HubError('应用版本不存在', 404, 'not_found')
    if row.state != 'published':
        raise HubError('只有已发布版本可以下架', 409, 'invalid_state')
    row.state = 'retired'
    db.session.commit()
    return jsonify(data=serialize(row, private=True))


def register_aihub_routes(app):
    app.register_blueprint(blueprint)
