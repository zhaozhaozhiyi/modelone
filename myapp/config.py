"""Minimal local defaults; deployment overlays can extend this module."""

from myapp.brand import BRAND, brand_asset, image_repository


APP_NAME = BRAND["name"]
APP_TITLE = BRAND["title"]
APP_DESCRIPTION = BRAND["description"]
APP_ICON = BRAND["logo_url"]
DOCUMENTATION_URL = BRAND["help_url"]
BUG_REPORT_URL = BRAND["support_url"]
GIT_URL = ""
REPOSITORY_ORG = image_repository("")
PUSH_REPOSITORY_ORG = image_repository("")
