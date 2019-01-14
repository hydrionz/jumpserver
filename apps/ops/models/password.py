# -*- coding: utf-8 -*-
#


from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _
from assets.models.utils import private_key_validator

from orgs.mixins import OrgModelMixin


class ChangePasswordAssetTask(OrgModelMixin):
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    username = models.CharField(max_length=128, verbose_name=_('Username'))
    assets = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, verbose_name=_("Asset"))
    comment = models.TextField(verbose_name=_('Comment'), blank=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Date created'))
    date_updated = models.DateTimeField(auto_now=True)
    date_last_run = models.DateTimeField(null=True, verbose_name=_('Date last run'))
    created_by = models.CharField(max_length=128, blank=True, verbose_name=_('Created by'))

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [('org_id', 'name')]


class ChangePasswordAssetModelMixin(models.Model):
    reason = models.CharField(max_length=128, default='-', blank=True, verbose_name=_('Reason'))
    interval = models.IntegerField(null=True, blank=True, help_text=_("Units: seconds"), verbose_name=_("Interval"))
    date_start = models.DateTimeField(db_index=True, default=timezone.now, verbose_name=_("Date start"))
    is_success = models.BooleanField(default=False, verbose_name=_('Is success'))


class ChangePasswordAssetTaskHistory(ChangePasswordAssetModelMixin):
    task = models.ForeignKey(ChangePasswordAssetTask, related_name='history', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date_start']


class ChangePasswordOneAssetTask(ChangePasswordAssetModelMixin):
    task = models.ForeignKey(ChangePasswordAssetTask, related_name='subtask', on_delete=models.CASCADE)
    asset = models.OneToOneField('assets.Asset', related_name='change_password_task', verbose_name=_('Asset'), null=True, on_delete=models.CASCADE)
    _password = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Password'))
    _public_key = models.TextField(max_length=4096, blank=True, verbose_name=_('SSH public key'))
    _private_key = models.TextField(max_length=4096, blank=True, null=True, verbose_name=_('SSH private key'), validators=[private_key_validator, ])
    _old_password = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Old password'))
    run_times = models.IntegerField(default=1, verbose_name=_('Run times'))
    date_last_run = models.DateTimeField(null=True, verbose_name=_('Date last run'))
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Date created'))
