# -*- coding: utf-8 -*-
#


from assets.models import AuthBook
from .base import CredentialBackend


class AuthBookBackend(CredentialBackend):

    def get_auth(self, asset, username):
        if asset is None or username is None:
            return {}

        instance = AuthBook.objects.filter(
            asset=asset, username=username
        ).latest_version().first()

        auth = instance.get_auth_local()

        return auth

    def filter(self, asset=None, username=None, latest=False, include_auth=False):
        return None

    def create(self, asset, username, auth_info):
        return None
