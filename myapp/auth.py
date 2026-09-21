"""Shared local-account login for Docker and Kubernetes deployments."""
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

from flask import flash, g, jsonify, redirect, request, session
from flask_appbuilder.security.forms import LoginForm_db
from flask_appbuilder.security.views import AuthDBView, expose
from flask_login import login_user, logout_user


def local_redirect(value, fallback):
    # Also accepts the absolute same-origin URLs sent by the existing frontend.
    if not value or '\\' in value or any(ord(c) < 32 for c in value):
        return fallback
    try:
        parsed = urlsplit(value)
    except ValueError:
        return fallback
    origin = urlsplit(request.host_url)
    if parsed.netloc and (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc):
        return fallback
    if parsed.scheme and not parsed.netloc:
        return fallback
    path = parsed.path or '/'
    if not path.startswith('/') or path.startswith('//'):
        return fallback
    return path + ('?' + parsed.query if parsed.query else '') + ('#' + parsed.fragment if parsed.fragment else '')


class ModelOneAuthDBView(AuthDBView):
    login_template = 'appbuilder/general/security/login_db.html'

    def finish_login(self, user):
        login_user(user, remember=False)
        from myapp import event_logger
        event_logger.log(user_id=user.id, action='login', duration_ms=0)
        # Preserve the existing first-login workspace setup for local accounts.
        if re.fullmatch(r'[a-z][a-z0-9-]*[a-z0-9]', user.username):
            from myapp.security import MyUserRemoteUserModelView_Base
            MyUserRemoteUserModelView_Base().post_add(user)
            target = Path('/data/k8s/kubeflow/pipeline/workspace') / user.username / 'pipeline/example'
            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(Path(__file__).parent / 'example/pipeline', target)

    @expose('/login/api/', methods=['GET', 'POST'])
    def login_api(self):
        # A username, query-string token or tenant parameter is not a credential.
        user = None
        if request.method == 'POST' and request.is_json:
            origin = request.headers.get('Origin')
            if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
                return jsonify(status=1, message='认证失败', result={}), 401
            data = request.get_json(silent=True) or {}
            if isinstance(data, dict):
                token = data.get('token', '')
                if isinstance(token, str) and token:
                    user = self.appbuilder.sm.load_user_from_header(token)
        if not user or not user.is_active:
            return jsonify(status=1, message='认证失败', result={}), 401
        self.finish_login(user)
        return jsonify(status=0, message='登录成功', result={})

    @expose('/login/', methods=['GET', 'POST'])
    def login(self):
        destination = local_redirect(request.args.get('login_url', ''), self.appbuilder.get_url_for_index)
        if g.user is not None and g.user.is_authenticated:
            return redirect(destination)
        form = LoginForm_db(meta={'csrf': True})
        if form.validate_on_submit():
            user = self.appbuilder.sm.auth_user_db(form.username.data, form.password.data)
            if user and user.is_active:
                self.finish_login(user)
                return redirect(destination)
            flash('账号或密码不正确，请联系管理员确认账号状态。', 'warning')
        return self.render_template(self.login_template, title=self.title, form=form, appbuilder=self.appbuilder)

    @expose('/logout')
    def logout(self):
        logout_user()
        session.clear()
        g.user = None
        return redirect('/login/')
