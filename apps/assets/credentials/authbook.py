#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from ..models import AuthBook
from .base import CredentialBackend

from common.utils import get_logger

logger = get_logger(__file__)


class AuthBookBackend(CredentialBackend):

    @staticmethod
    def _get_latest(items=None):
        if not items:
            return None
        try:
            item = items.latest()
        except Exception as e:
            logger.debug(e)
            return None
        else:
            return item

    def _filter_latest(self, items):
        items_latest = []
        for username in set([item.username for item in items]):
            items_username = items.filter(username=username)
            for asset in set([item.asset for item in items_username]):
                items_username_asset = items_username.filter(asset=asset)
                item = self._get_latest(items_username_asset)
                if item is not None:
                    items_latest.append(item)
        return items_latest

    def _get_items(self, pk=None, asset=None, username=None, latest=False):
        if pk:
            items = AuthBook.objects.filter(pk=pk)
            return items

        items = AuthBook.objects.all()
        if asset:
            items = items.filter(asset=asset)
        if username:
            items = items.filter(username=username)
        if latest:
            items = self._filter_latest(items)
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
        item = AuthBook.objects.create(
            name=name, asset=asset, username=username, comment=comment
        )

        if isinstance(auth_info, dict):
            auth = {
                'password': auth_info.get('password', None),
                'public_key': auth_info.get('public_key', None),
                'private_key': auth_info.get('private_key', None)
            }
            item.set_auth(**auth)

        logger.debug('Create auth book item {}@{}'.format(username, asset))
        return item

    def post_credential(self, name=None, asset=None, username=None,
                        comment=None, auth_info=None):

        item = self._post_item(name, asset, username, comment=comment,
                               auth_info=auth_info)
        return self._to_json(item)

    def _to_json(self, item, include_auth=False):
        data = {
            'id': item.id,
            'name': item.name,
            'username': item.username,
            'asset': item.asset.id,
            'comment': item.comment,
            'date_created': item.date_created,
            'date_updated': item.date_updated,
            'created_by': item.created_by,
            'org_id': item.org_id,
        }

        if include_auth:
            auth = item.get_auth_local()
            data.update(auth)

        return data

