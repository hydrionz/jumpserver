#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from django.db import models
from django.utils.translation import ugettext as _


from .base import AssetUser
from common.utils import get_logger


logger = get_logger(__file__)


class AuthBook(AssetUser):
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset'))

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)

    @classmethod
    def get_latest(cls, items=None):
        if not items:
            return None
        try:
            item = items.latest()
        except Exception as e:
            logger.debug(e)
            return None
        else:
            return item

    @classmethod
    def filter_latest(cls, items):
        items_latest = []
        for username in set([item.username for item in items]):
            items_username = items.filter(username=username)
            for asset in set([item.asset for item in items_username]):
                items_username_asset = items_username.filter(asset=asset)
                item = cls.get_latest(items_username_asset)
                if item is not None:
                    items_latest.append(item)
        return items_latest

    @classmethod
    def get_items(cls, asset=None, username=None, latest=False):
        items = AuthBook.objects.all()
        if asset:
            items = items.filter(asset=asset)
        if username:
            items = items.filter(username=username)
        if latest:
            items = cls.filter_latest(items)
        return items

    @classmethod
    def create_item(cls, name=None, asset=None, username=None, comment=None,
                    auth_info=None):

        item = cls.objects.create(
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

    def _to_json(self, include_auth=False):
        data = {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'comment': self.comment,
            'date_created': self.date_created,
            'date_updated': self.date_updated,
            'created_by': self.created_by,
            'org_id': self.org_id,
            'asset_id': self.asset.id,
        }

        if include_auth:
            auth = self.get_auth_local()
            data.update(auth)

        return data

    class Meta:
        get_latest_by = 'date_updated'
