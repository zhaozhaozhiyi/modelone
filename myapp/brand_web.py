"""Public browser metadata routes, registered with the shared brand provider."""
import json
from flask import abort


def register_brand_routes(app, brand):
    @app.route('/myapp/brand.js')
    def modelone_brand_config():
        return app.response_class(brand.browser_config_script(), mimetype='application/javascript',
                                  headers={'Cache-Control': 'no-store'})

    @app.route('/myapp/manifest/<app_name>.json')
    def modelone_web_manifest(app_name):
        if app_name not in brand.BROWSER_APPS:
            abort(404)
        return app.response_class(json.dumps(brand.public_manifest(app_name), ensure_ascii=False),
                                  mimetype='application/manifest+json',
                                  headers={'Cache-Control': 'no-store'})
