# -*- coding: utf-8 -*-
#

import abc


class CredentialBackend(object):

    @abc.abstractclassmethod
    def get(self, asset, username):
        """
        :param asset: Asset object
        :param username: str
        :return: AuthBook object
        """
        return None

    @abc.abstractclassmethod
    def filter(self, asset=None, username=None, latest=True, include_auth=False):
        return None

    @abc.abstractclassmethod
    def create(self, asset, username, auth_info):
        return None

