#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from django.db import models
from django.utils.translation import ugettext as _


from .base import AssetUser


class AuthBook(AssetUser):
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset'))

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)

    class Meta:
        get_latest_by = 'date_updated'
