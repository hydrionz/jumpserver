#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from ..models import AuthBook
from .base import CredentialBackend

from common.utils import get_logger

logger = get_logger(__file__)


class AuthBookBackend(CredentialBackend):

    def _get_items(self, pk=None, asset=None, username=None, latest=False):
        if pk:
            items = AuthBook.objects.filter(pk=pk)
            return items
        else:
            items = AuthBook.get_items(asset, username, latest)
            return items

    def get_auth(self, asset, username):
        item = self._get_items(asset=asset, username=username, latest=True)
        if item:
            return item[0].get_auth_local()
        else:
            return {}

    def get_credentials(self, pk=None, asset=None, username=None, latest=False,
                        include_auth=False):

        credentials = []
        items = self._get_items(pk, asset, username, latest)
        for item in items:
            data = self._to_json(item, include_auth=include_auth)
            credentials.append(data)
        return credentials

    def _post_item(self, name=None, asset=None, username=None, comment=None,
                   auth_info=None):

        if name is None:
            name = '{}@{}'.format(username, asset)

        item = AuthBook.create_item(name=name, asset=asset, username=username,
                                    comment=comment, auth_info=auth_info)
        return item

    def post_credential(self, name=None, asset=None, username=None,
                        comment=None, auth_info=None):

        item = self._post_item(name, asset, username, comment=comment,
                               auth_info=auth_info)
        return self._to_json(item)

    def _to_json(self, item, include_auth=False):
        return item._to_json(include_auth=include_auth)


