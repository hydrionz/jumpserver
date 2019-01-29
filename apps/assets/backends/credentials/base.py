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
    def filter(self, asset=None, username=None, latest=True):
        """
        :param asset:
        :param username:
        :param latest:
        :return: QuerySet object or []
        """
        return None

    @abc.abstractclassmethod
    def create(self, name, asset, username, comment, org_id,
               password=None, public_key=None, private_key=None):
        """
        :param name:
        :param asset: Asset object
        :param username:
        :param comment:
        :param org_id: Organization object id
        :param password:
        :param public_key:
        :param private_key:
        :return: AuthBook object
        """
        return None
