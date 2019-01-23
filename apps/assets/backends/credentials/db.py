# -*- coding: utf-8 -*-
#


from assets.models import AuthBook
from .base import CredentialBackend


class AuthBookBackend(CredentialBackend):

    def get_auth(self, asset, username):
        queryset = AuthBook.objects.filter(asset=asset, username=username)
        instance = queryset.latest_version().first()
        auth = instance.get_auth_local() if instance else {}
        return auth

    def filter(self, asset=None, username=None, latest=False, include_auth=False):
        return None

    def create(self, asset, username, auth_info):
        return None
