"""Authenticated Label Studio endpoints, registered independently of FAB views."""
import json

from flask import Blueprint, Response, current_app, g, jsonify, request
from werkzeug.exceptions import BadRequest

from myapp.label_studio import LabelStudioClient, LabelStudioError
from myapp.label_studio_sso import sign_user


def register_label_studio_routes(app, client_class=LabelStudioClient):
    blueprint = Blueprint('label_studio', __name__, url_prefix='/label_studio/api')

    @blueprint.before_request
    def require_access():
        # Check again locally: these routes must also be safe in isolated apps.
        user = getattr(g, 'user', None)
        if not user or not user.get_id() or not getattr(user, 'active', False):
            return jsonify(message='请先登录平台', status=401), 401
        if not current_app.config.get('LABEL_STUDIO_ENABLED', False):
            return jsonify(message='标注服务尚未启用', status=503), 503

    @blueprint.errorhandler(LabelStudioError)
    def adapter_error(error):
        return jsonify(message=str(error), status=error.status), error.status

    @blueprint.errorhandler(BadRequest)
    def invalid_json(error):
        return jsonify(message='请输入有效的 JSON', status=400), 400

    @blueprint.after_request
    def private_response(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    def call(method, *args, **kwargs):
        client = client_class(current_app.config['LABEL_STUDIO_INTERNAL_URL'],
                              authorization=request.headers.get('X-Label-Studio-Authorization'),
                              timeout=current_app.config.get('LABEL_STUDIO_TIMEOUT', (5, 60)))
        try:
            return getattr(client, method)(*args, **kwargs)
        finally:
            client.close()

    def payload():
        # Bound before parsing even if the request uses chunked transfer encoding.
        limit = 10 * 1024 * 1024
        if request.content_length is not None and request.content_length > limit:
            raise LabelStudioError('单次导入不能超过 10 MiB，请分批导入', 413)
        if not request.is_json:
            raise LabelStudioError('请使用 application/json', 400)
        raw = request.stream.read(limit + 1)
        if len(raw) > limit:
            raise LabelStudioError('单次导入不能超过 10 MiB，请分批导入', 413)
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError):
            raise BadRequest() from None

    @blueprint.get('/access')
    def access():
        # Nginx auth_request checks the real platform session, not username cookies.
        try:
            assertion = sign_user(g.user)
        except ValueError:
            return jsonify(message='标注平台单点登录尚未配置', status=503), 503
        return Response(status=204, headers={'X-Modelone-Assertion': assertion})

    @blueprint.get('/config')
    def config():
        return jsonify(url=current_app.config.get('LABEL_STUDIO_PUBLIC_URL', '/labelstudio/'),
                       authentication='platform-session', single_sign_on=True)

    @blueprint.get('/status')
    def status():
        return jsonify(call('health'))

    @blueprint.route('/projects', methods=['GET', 'POST'])
    def projects():
        if request.method == 'GET':
            try:
                page = int(request.args.get('page', '1'))
                page_size = int(request.args.get('page_size', '20'))
                if page < 1 or not 1 <= page_size <= 100:
                    raise ValueError()
            except ValueError:
                raise LabelStudioError('分页参数无效', 400) from None
            return jsonify(call('projects', page, page_size))
        data = payload()
        if (not isinstance(data, dict) or not isinstance(data.get('title'), str)
                or not data['title'].strip() or len(data['title']) > 200
                or not isinstance(data.get('label_config'), str) or not data['label_config'].strip()
                or not isinstance(data.get('description', ''), str)
                or set(data) - {'title', 'description', 'label_config'}):
            raise LabelStudioError('请提供 title、label_config，可选 description', 400)
        return jsonify(call('create_project', data)), 201

    @blueprint.get('/projects/<int:project_id>')
    def project(project_id):
        return jsonify(call('project', project_id))

    @blueprint.post('/projects/<int:project_id>/import')
    def import_tasks(project_id):
        tasks = payload()
        if (not isinstance(tasks, list) or not 1 <= len(tasks) <= 1000
                or any(not isinstance(task, dict) or not isinstance(task.get('data'), dict)
                       or not task['data'] or set(task) - {'data', 'predictions', 'meta'} for task in tasks)):
            raise LabelStudioError('请提供 1–1000 条任务，每条包含 data 对象，可选 predictions 和 meta', 400)
        return jsonify(call('import_tasks', project_id, tasks))

    @blueprint.get('/projects/<int:project_id>/export')
    def export_tasks(project_id):
        all_tasks = request.args.get('all_tasks', 'false').lower()
        if all_tasks not in ('true', 'false'):
            raise LabelStudioError('all_tasks 只能为 true 或 false', 400)
        tasks = call('export_tasks', project_id, all_tasks == 'true')
        return Response(json.dumps(tasks, ensure_ascii=False), content_type='application/json; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename="modelone-labels-%d.json"' % project_id})

    app.register_blueprint(blueprint)
