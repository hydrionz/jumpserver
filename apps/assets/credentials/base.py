#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import abc


class CredentialBackend(metaclass=abc.ABCMeta):

    @abc.abstractclassmethod
    def _get_items(self, pk=None, asset=None, username=None, latest=False):
        return None

    @abc.abstractclassmethod
    def get_auth(self, asset, username):
        return None

    @abc.abstractclassmethod
    def get_credentials(self, pk=None, asset=None, username=None,
                        latest=False, include_auth=False):
        return None

    @abc.abstractclassmethod
    def _post_item(self, name=None, asset=None, username=None, comment=None,
                   auth_info=None):
        return None

    @abc.abstractclassmethod
    def post_credential(self, name=None, asset=None, username=None,
                        comment=None, auth_info=None):
        return None

    @abc.abstractclassmethod
    def _to_json(self, item, include_auth=False):
        return None
