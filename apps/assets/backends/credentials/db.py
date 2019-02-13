# -*- coding: utf-8 -*-
#


from assets.models import AuthBook
from .base import CredentialBackend


class AuthBookBackend(CredentialBackend):

    def get(self, pk=None, asset=None, username=None):
        if pk:
            instance = AuthBook.objects.filter(id=pk).first()
        elif asset and username:
            queryset = AuthBook.objects.filter(asset=asset, username=username)
            instance = queryset.latest_version().first()
        else:
            instance = None
        return instance

    def filter(self, asset=None, username=None, latest=False):
        queryset = AuthBook.objects.all()
        if asset:
            queryset = queryset.filter(asset=asset)
        if username:
            queryset = queryset.filter(username=username)
        if latest:
            queryset = queryset.latest_version()
        return queryset

    def create(self, name, asset, username, comment, org_id,
               password=None, public_key=None, private_key=None):

        obj = AuthBook.objects.create(
            name=name, asset=asset, username=username,
            comment=comment, org_id=org_id
        )
        obj.set_auth(password, private_key, public_key)
        return obj
