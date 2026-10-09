"""Load upstream settings in this module, then enable modelOne identity checks.

Upstream settings initialize Sentry while Django is still importing the
settings module, so importing them as a second module causes a recursive read.
"""
from pathlib import Path

upstream = Path(__file__).with_name('label_studio.py')
exec(compile(upstream.read_text(), str(upstream), 'exec'), globals())

MIDDLEWARE.append('modelone_sso.ModeloneSSOMiddleware')
