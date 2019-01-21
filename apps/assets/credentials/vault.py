#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from .base import CredentialBackend


class VaultBackend(CredentialBackend):

    def get_items(self, asset=None, username=None):
        return None

    def get_latest(self, items=None):
        return None

    def get_item_latest(self, asset, username):
        return None

    def get_auth(self, asset, username):
        return None

    def create_item(self, asset, username):
        return None
