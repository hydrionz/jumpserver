#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import abc


class CredentialBackend(metaclass=abc.ABCMeta):

    @abc.abstractclassmethod
    def get_items(self, asset=None, username=None):
        return None

    @abc.abstractclassmethod
    def get_latest(self, items=None):
        return None

    @abc.abstractclassmethod
    def get_item_latest(self, asset, username):
        return None

    @abc.abstractclassmethod
    def get_auth(self, asset, username):
        return None

    @abc.abstractclassmethod
    def create_item(self, asset, username):
        return None
