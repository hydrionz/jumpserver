#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


from django.db import models
from django.utils.translation import ugettext as _

from common.utils import get_logger
from .base import AssetUser

logger = get_logger(__file__)


class AuthBook(AssetUser):
    """
    批量改密任务执行后，用来存放执行成功的 <username, asset, password> 对应关系
    当系统用户/管理用户使用密码时，从这里获取。
    """
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE,
                              verbose_name=_('Asset'))

    @classmethod
    def get_matched_item_latest(cls, username, asset):
        try:
            logger.debug("Try to get {}@{} auth info from AuthBook".
                         format(username, asset))
            item = cls.objects.filter(username=username, asset=asset).latest()
        except Exception as e:
            logger.debug("Get auth info from AuthBook error: {}".format(e))
            return None
        else:
            logger.debug("Get auth info from AuthBook success")
            return item

    @classmethod
    def create_item(cls, username, password, asset):
        item = cls.objects.create(
            name='{}@{}'.format(username, asset),
            username=username, asset=asset
        )
        item.set_auth(password=password)
        logger.debug('Create auth book item {}@{}'.format(username, asset))
        return item

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)

    class Meta:
        get_latest_by = 'date_updated'
