#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from django.db import models
from django.utils.translation import ugettext as _


from .base import AssetUser
from orgs.mixins import OrgManager


class AuthBookQuerySet(models.QuerySet):

    def latest_version(self):
        return self.filter(is_latest=True)


class AuthBookManager(OrgManager):
    pass


class AuthBook(AssetUser):
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset'))
    is_latest = models.BooleanField(default=False, verbose_name=_('Latest'))
    version_count = models.IntegerField(default=1, verbose_name=_('Version count'))

    objects = AuthBookManager.from_queryset(AuthBookQuerySet)()

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)

    def set_latest(self):
        previous_obj = self._remove_previous_latest()
        self.set_version_count(previous_obj)
        self.is_latest = True
        self.save()

    def set_version_count(self, previous_obj):
        if previous_obj:
            self.version_count = previous_obj.version_count + 1
        else:
            self.version_count = 1

    def _remove_previous_latest(self):
        previous_obj = self.__class__.objects.filter(
            username=self.username, asset=self.asset,
        ).latest_version().first()
        if previous_obj:
            previous_obj.is_latest = False
            previous_obj.save()
        return previous_obj
