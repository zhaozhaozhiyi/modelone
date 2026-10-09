"""Trust only signed modelOne identities supplied by the protected Nginx proxy."""
import base64
import hashlib
import hmac
import json
import os
import time

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseForbidden
from organizations.models import Organization


def verify_assertion(value, secret, now=None):
    if len(secret) < 32 or len(value) > 4096:
        raise ValueError('Invalid SSO configuration or assertion')
    try:
        data, signature = value.split('.', 1)
        expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            raise ValueError('Invalid SSO signature')
        payload = json.loads(base64.urlsafe_b64decode(data + '=' * (-len(data) % 4)))
        if not isinstance(payload, dict):
            raise ValueError('Invalid SSO payload')
        age = int(time.time() if now is None else now) - payload['iat']
        if (payload.get('aud') != 'label-studio' or not isinstance(payload.get('sub'), str)
                or not payload['sub'] or len(payload['sub']) > 100
                or not isinstance(payload.get('username'), str) or not payload['username']
                or len(payload['username']) > 200 or type(payload['iat']) is not int
                or age < -10 or age > 60):
            raise ValueError('Invalid SSO claims')
        return payload
    except (TypeError, KeyError, UnicodeError, ValueError) as error:
        raise ValueError('Invalid SSO assertion') from error


class ModeloneSSOMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.secret = os.environ.get('MODELONE_LABEL_STUDIO_SSO_SECRET', '')

    def __call__(self, request):
        assertion = request.META.get('HTTP_X_MODELONE_ASSERTION')
        if assertion:
            try:
                claims = verify_assertion(assertion, self.secret)
                email = 'modelone-' + hashlib.sha256(claims['sub'].encode()).hexdigest()[:32] + '@users.invalid'
                User = get_user_model()
                with transaction.atomic():
                    user, created = User.objects.get_or_create(
                        email=email, defaults={'username': claims['username'],
                                               'first_name': claims['username'], 'is_active': True})
                    if created:
                        user.set_unusable_password()
                        user.save(update_fields=['password'])
                    elif user.first_name != claims['username']:
                        user.first_name = claims['username']
                        user.save(update_fields=['first_name'])
                    if not user.is_active:
                        raise ValueError('Inactive SSO user')
                    organization = Organization.objects.first()
                    if organization is None:
                        raise ValueError('Label Studio organization is not initialized')
                    organization.add_user(user)
                    if user.active_organization_id != organization.pk:
                        user.active_organization = organization
                        user.save(update_fields=['active_organization'])
                request.user = user
                request._cached_user = user
            except ValueError:
                return HttpResponseForbidden('Invalid modelOne session')
        return self.get_response(request)
