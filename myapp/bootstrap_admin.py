"""Create the initial administrator without a fixed password or resetting users."""
from myapp import app, appbuilder
from myapp.auth_config import read_secret
import os


def bootstrap():
    manager = appbuilder.sm
    if manager.find_user(username='admin'):
        print('Existing administrator preserved')
        return
    password = read_secret('MODELONE_ADMIN_PASSWORD', minimum=16)
    role = manager.find_role('Admin') or manager.add_role('Admin')
    user = manager.add_user(username='admin', first_name='admin', last_name='admin',
                            email=os.environ.get('MODELONE_ADMIN_EMAIL', 'admin@modelone.invalid'),
                            role=role, password=password)
    if not user:
        raise RuntimeError('Initial administrator could not be created')
    print('Initial administrator created')


if __name__ == '__main__':
    with app.app_context():
        bootstrap()
