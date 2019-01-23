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
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE,
                              verbose_name=_('Asset'))
    is_latest = models.BooleanField(default=False, verbose_name=_('Latest'))

    objects = AuthBookManager.from_queryset(AuthBookQuerySet)()

    def set_latest(self):
        queryset = self.__class__.objects.filter(username=self.username,
                                                 asset=self.asset)
        instance = queryset.latest_version().first()
        if instance:
            instance.is_latest = False
            instance.save()

        self.is_latest = True
        self.save()

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)

    class Meta:
        get_latest_by = 'date_updated'
