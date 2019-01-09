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
    批量改密任务执行后，存放执行成功的 <username, asset> 对应关系
    """
    asset = models.ForeignKey(
        'assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset')
    )

    @classmethod
    def get_latest_item_by_username_asset(cls, username, asset):
        try:
            item = AuthBook.objects.filter(username=username, asset=asset).latest()
            logger.debug('Get auth book item {}@{}'.format(username, asset))
        except AuthBook.DoesNotExist as e:
            logger.debug(
                'msg: {} (username: {}, asset: {})'.format(e, username, asset)
            )
            item = None
        return item

    @classmethod
    def create_item(cls, username, password, asset):
        item = cls.objects.create(
            name='{}@{}'.format(username, asset), username=username,
            asset=asset
        )
        item.set_auth(password=password)
        logger.debug('Create auth book item {}@{}'.format(username, asset))
        return item

    class Meta:
        get_latest_by = 'date_created'

    def __str__(self):
        return '{}@{}'.format(self.username, self.asset)
