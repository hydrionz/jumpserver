# -*- coding: utf-8 -*-
#

import uuid
import json
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from orgs.mixins import OrgModelMixin
from assets.models import AuthBook
from common.validators import alphanumeric
from common.utils import get_signer, get_logger, encrypt_password
from common.utils import random_password_gen
from assets.tasks import clean_hosts, const
from ..ansible import AdHocRunner, AnsibleError
from ..inventory import JMSInventory

logger = get_logger(__file__)
signer = get_signer()
TASK_NAME_CHANGE_ASSET_PASSWORD = 'change_asset_password'


class ChangeAssetPasswordTask(OrgModelMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    username = models.CharField(max_length=32, verbose_name=_('Username'), validators=[alphanumeric])
    hosts = models.ManyToManyField('assets.Asset')
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=128, null=True, verbose_name=_('Created by'))

    def __str__(self):
        return self.name

    @staticmethod
    def get_tasks(username, password):
        tasks = list()
        tasks.append({
            'name': TASK_NAME_CHANGE_ASSET_PASSWORD,
            'action': {
                'module': 'user',
                'args': 'name={} password={} update_password=always'.format(
                    username, encrypt_password(password, salt="K3mIlKK")
                ),
            }
        })
        return tasks

    def run(self, record=True):
        if record:
            return self._run_and_record()
        else:
            return self._run_only()

    def _run_and_record(self):
        history = ChangeAssetPasswordTaskHistory(task=self)
        try:
            history.date_start = timezone.now()
            results = self._run_only()
            result = self.handle_results(results)
            history.result = result
            return result
        except Exception as e:
            logger.warning(e)
            return {}
        finally:
            history.is_finished = True
            history.date_finished = timezone.now()
            history.save()

    def _run_only(self):
        results = []
        hosts = clean_hosts(self.hosts.all())
        if not hosts:
            return {}
        for host in hosts:
            task_name = _('Change user <{}> password to asset <{}>.'
                          .format(self.username, host))
            password = random_password_gen()
            tasks = self.get_tasks(self.username, password)
            inventory = JMSInventory(assets=[host], run_as_admin=True)
            runner = AdHocRunner(inventory, options=const.TASK_OPTIONS)
            try:
                result = runner.run(
                    tasks=tasks,
                    pattern='all',
                    play_name=task_name
                )
            except AnsibleError as e:
                logger.warn('Failed run adhoc {}, {}'.format(task_name, e))
            else:
                result.results_summary.update({
                    'password': password,
                    'hostname': host.hostname,
                })
                results.append((result.results_raw, result.results_summary))

        return results

    def handle_results(self, results):
        result = {
            'count': {
                'total': len(results),
                'success': 0,
                'failed': 0,
            },
            'detail': {
                'failed': {},
                'success': {}
            }
        }
        success = failed = 0
        for raw, summary in results:
            hostname = summary.get('hostname')
            if summary.get('success'):
                success += 1
                result['detail']['success'].update({hostname: ''})
                password = summary.get('password')
                asset = self.hosts.all().filter(hostname=hostname).first()
                AuthBook.create_item(self.username, password, asset)
            else:
                failed += 1
                msg = summary.\
                    get('dark').\
                    get(hostname).\
                    get(TASK_NAME_CHANGE_ASSET_PASSWORD).\
                    get('msg')
                result['detail']['failed'].update({hostname: msg})
        result['count'].update({'success': success, 'failed': failed})
        return result


class ChangeAssetPasswordTaskHistory(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    task = models.ForeignKey('ops.ChangeAssetPasswordTask', on_delete=models.CASCADE, verbose_name=_('Change password task'))
    _result = models.TextField(blank=True, null=True, verbose_name=_('Result'))
    is_finished = models.BooleanField(default=False)
    date_start = models.DateTimeField(null=True)
    date_finished = models.DateTimeField(null=True)

    @property
    def result(self):
        if self._result:
            return json.loads(self._result)
        else:
            return {}

    @result.setter
    def result(self, item):
        self._result = json.dumps(item)
