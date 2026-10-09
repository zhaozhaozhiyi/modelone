"""Run against a migrated local database: python -m myapp.aihub.test_portal."""
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from myapp import app, db
from myapp.aihub.models import ApplicationVersion, Invocation
from myapp.security import MyUser


class Endpoint(BaseHTTPRequestHandler):
    slug = ''
    revision = 'sha256:aihub-smoke'

    def log_message(self, *_args):
        pass

    def reply(self, body):
        raw = json.dumps(body).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/metadata':
            self.reply({'application_id': self.slug, 'version': '1.0.0',
                        'revision': self.revision})
        elif self.path == '/health':
            self.reply({'status': 'ok'})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != '/predict':
            self.send_error(404)
            return
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.reply({'result': {'echo': payload['inputs']['text']}})


class PortalTest(unittest.TestCase):
    def test_publish_predict_and_retire(self):
        slug = 'aihub-smoke-%d' % int(time.time() * 1000000)
        Endpoint.slug = slug
        Endpoint.revision = 'sha256:aihub-smoke'
        server = ThreadingHTTPServer(('127.0.0.1', 0), Endpoint)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        old_hosts = app.config.get('AIHUB_ENDPOINT_HOSTS')
        try:
            with app.app_context():
                app.config['AIHUB_ENDPOINT_HOSTS'] = ('127.0.0.1',)
                admin = db.session.query(MyUser).filter_by(username='admin').first()
                self.assertIsNotNone(admin, 'Local admin account is required')
                headers = {'Authorization': admin.secret}
                client = app.test_client()
                payload = {
                    'slug': slug, 'version': '1.0.0', 'name': 'AIHub Smoke',
                    'summary': 'Temporary integration test', 'category': '自然语言',
                    'task': 'echo', 'model_source': 'https://example.org/aihub-smoke',
                    'license_name': 'Apache-2.0', 'weight_digest': '',
                    'visibility': 'public', 'project_id': None,
                    'input_schema': {'type': 'object', 'properties': {'text': {'type': 'string'}},
                                     'required': ['text'], 'additionalProperties': False},
                    'output_schema': {'type': 'object', 'properties': {'echo': {'type': 'string'}},
                                      'required': ['echo']},
                    'endpoint_url': 'http://127.0.0.1:%d' % server.server_address[1],
                    'endpoint_revision': Endpoint.revision, 'credential_env': '',
                }
                with patch('myapp.aihub.web.validate_endpoint_destination'), \
                     patch('myapp.aihub.protocol.validate_endpoint_destination'):
                    self.run_flow(client, payload, headers, slug)
        finally:
            with app.app_context():
                app.config['AIHUB_ENDPOINT_HOSTS'] = old_hosts
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def run_flow(self, client, payload, headers, slug):
        record_id = None
        try:
            created = client.post('/aihub/api/admin/apps', json=payload, headers=headers)
            self.assertEqual(created.status_code, 201, created.get_json())
            record_id = created.get_json()['data']['id']
            self.assertEqual(client.get('/aihub/api/apps/' + slug, headers=headers).status_code, 404)
            published = client.post('/aihub/api/admin/apps/%d/publish' % record_id, headers=headers)
            self.assertEqual(published.status_code, 200, published.get_json())
            detail = client.get('/aihub/api/apps/' + slug, headers=headers)
            self.assertEqual(detail.status_code, 200)
            self.assertNotIn('endpoint_url', detail.get_json()['data']['application'])
            page = client.get('/aihub/', headers=headers)
            self.assertEqual(page.status_code, 200)
            page.close()
            prediction = '/aihub/api/apps/%s/versions/1.0.0/predict' % slug
            success = client.post(prediction, json={'inputs': {'text': 'hello'}}, headers=headers)
            self.assertEqual(success.status_code, 200, success.get_json())
            self.assertEqual(success.get_json()['data']['result'], {'echo': 'hello'})
            invalid = client.post(prediction, json={'inputs': {}}, headers=headers)
            self.assertEqual(invalid.status_code, 400)
            Endpoint.revision = 'sha256:changed'
            mismatch = client.post(prediction, json={'inputs': {'text': 'secret-input'}}, headers=headers)
            self.assertEqual(mismatch.status_code, 409, mismatch.get_json())
            self.assertEqual(mismatch.get_json()['error']['code'], 'revision_mismatch')
            invocations = db.session.query(Invocation).filter_by(version_id=record_id).all()
            self.assertEqual([entry.status for entry in invocations], ['success', 'failed'])
            self.assertEqual(client.put('/aihub/api/admin/apps/%d' % record_id,
                                        json=payload, headers=headers).status_code, 409)
            retired = client.post('/aihub/api/admin/apps/%d/retire' % record_id, headers=headers)
            self.assertEqual(retired.status_code, 200)
            self.assertEqual(client.get('/aihub/api/apps/' + slug, headers=headers).status_code, 404)
        finally:
            if record_id is not None:
                db.session.query(Invocation).filter_by(version_id=record_id).delete()
                db.session.query(ApplicationVersion).filter_by(id=record_id).delete()
                db.session.commit()


if __name__ == '__main__':
    unittest.main()
