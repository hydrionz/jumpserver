#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from .base import CredentialBackend


class VaultBackend(CredentialBackend):

    def _get_items(self, pk=None, asset=None, username=None, latest=False):
        return None

    def get_auth(self, asset, username):
        return None

    def get_credentials(self, pk=None, asset=None, username=None,
                        latest=False, include_auth=False):
        return None

    def _post_item(self, name=None, asset=None, username=None, comment=None,
                   auth_info=None):
        return None

    def post_credential(self, name=None, asset=None, username=None,
                        comment=None, auth_info=None):
        return None

    def _to_json(self, item, include_auth=False):
        return None

