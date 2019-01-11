#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


from django.db import models
from django.utils.translation import ugettext as _

from .base import AssetUser


class AuthBook(AssetUser):
    """
    批量改密任务执行后，用来存放执行成功的 <username, asset, password> 对应关系
    当系统用户/管理用户使用密码时，从这里获取。
    """
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset'))

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)

    class Meta:
        get_latest_by = 'date_created'
