#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from ..models import AuthBook
from .base import CredentialBackend

from common.utils import get_logger

logger = get_logger(__file__)


class AuthBookBackend(CredentialBackend):

    def get_items(self, asset=None, username=None):
        items = AuthBook.objects.filter(asset=asset, username=username)
        logger.debug('Get auth book items: {}'.format(items))
        return items

    def get_latest(self, items=None):
        if not items:
            return None

        try:
            item = items.latest()
        except Exception as e:
            logger.debug(e)
            return None
        else:
            return item

    def get_item_latest(self, asset, username):
        items = self.get_items(asset, username)
        item = self.get_latest(items)
        logger.debug('Get auth book item latest: {}'.format(item))
        return item

    def get_auth(self, asset, username):
        item = self.get_item_latest(asset, username)
        if item is None:
            auth = {}
        else:
            auth = item.get_auth_local()
        return auth

    def create_item(self, asset, username, auth_info=None):
        name = '{}@{}'.format(username, asset)
        item = AuthBook.objects.create(name=name, asset=asset, username=username)
        if isinstance(auth_info, dict):
            auth = {
                'password': auth_info.get('password', None),
                'public_key': auth_info.get('public_key', None),
                'private_key': auth_info.get('private_key', None)
            }
            item.set_auth(**auth)
        logger.debug('Create auth book item {}@{}'.format(username, asset))
        return item
