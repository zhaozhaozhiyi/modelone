from datetime import datetime

from flask_appbuilder import Model
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint


class ApplicationVersion(Model):
    __tablename__ = 'aihub_application_version'
    __table_args__ = (UniqueConstraint('slug', 'version', name='uq_aihub_slug_version'),)

    id = Column(Integer, primary_key=True)
    slug = Column(String(80), nullable=False, index=True)
    version = Column(String(40), nullable=False)
    name = Column(String(200), nullable=False)
    summary = Column(String(2000), nullable=False, default='')
    category = Column(String(40), nullable=False)
    task = Column(String(100), nullable=False, default='')
    model_source = Column(String(500), nullable=False)
    license_name = Column(String(100), nullable=False)
    weight_digest = Column(String(200), nullable=False, default='')
    visibility = Column(String(20), nullable=False, default='public')
    project_id = Column(Integer, ForeignKey('project.id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    state = Column(String(20), nullable=False, default='draft')
    input_schema = Column(Text, nullable=False)
    output_schema = Column(Text, nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    endpoint_revision = Column(String(200), nullable=False)
    credential_env = Column(String(100), nullable=False, default='')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    published_by_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)


class Invocation(Model):
    __tablename__ = 'aihub_invocation'

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('aihub_application_version.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    status = Column(String(20), nullable=False)
    error_type = Column(String(60), nullable=False, default='')
    duration_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
