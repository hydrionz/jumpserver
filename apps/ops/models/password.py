# -*- coding: utf-8 -*-
#

import uuid
import json
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from orgs.mixins import OrgModelMixin
from assets.models import AuthBook
from assets.tasks import clean_hosts, const
from common.validators import alphanumeric
from common.utils import get_signer, get_logger, encrypt_password, \
    random_password_gen
from ..ansible import AdHocRunner, AnsibleError
from ..inventory import JMSInventory

logger = get_logger(__file__)
signer = get_signer()


class RunAsUser:
    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password

    def _to_secret_json(self):
        """ Use when check bulk change asset password is valid"""
        return {
            'name': self.name,
            'username': self.username,
            'password': self.password,
        }


class ChangeAssetPasswordTask(OrgModelMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    username = models.CharField(max_length=32, verbose_name=_('Username'), validators=[alphanumeric])
    hosts = models.ManyToManyField('assets.Asset', verbose_name=_('Asset'))
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=128, null=True, verbose_name=_('Created by'))

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [('org_id', 'name')]

    @property
    def run_times(self):
        return len(self.changeassetpasswordtaskhistory_set.all())

    @property
    def hosts_name(self):
        return [host.hostname for host in self.hosts.all().order_by('hostname')]

    def run(self, record=True):
        if record:
            return self._run_and_record()
        else:
            return self._run_only()

    def _run_and_record(self):
        history = ChangeAssetPasswordTaskHistory(task=self)
        try:
            history.date_start = timezone.now()
            result = self._run_only()
            history.result = result
            history.is_success = True
            return result
        except Exception as e:
            logger.warning(e)
            history.is_success = False
            return {}
        finally:
            history.date_finished = timezone.now()
            history.save()

    def _run_only(self):
        """
        result = {
            'count': {
                'total': 0, 'success': 0, 'failed': 0,
            },
            'detail': {
                'failed': [], 'success': [{'hostname': 'xxx', 'id': '', 'msg': ''},]
            },
            'msg': 'Success',
        }
        :return: result
        """
        result = {
            'count': {'total': 0, 'success': 0, 'failed': 0},
            'detail': [],
            'msg': 'Success',
            'username': self.username,
        }

        count_success = count_failed = 0
        detail = []

        if self.username == 'root':
            msg = _('Change <{}> password is not allowed'.format(self.username))
            logger.debug(msg)
            result.update({'msg': msg})
            return result

        hosts = clean_hosts(self.hosts.all())
        if not hosts:
            msg = _('Change <{}> password but assets is empty.'.format(self.username))
            logger.debug(msg)
            result.update({'msg': msg})
            return result

        for host in hosts:
            password = random_password_gen()
            change_result = self._change_password_a_asset(password, host)

            if self.is_success(change_result):
                verify_result = self._verify_password_a_asset(password, host)

                if self.is_success(verify_result):
                    count_success += 1
                    msg = '-'
                    success = True
                    AuthBook.create_item(self.username, password, host)
                else:
                    count_failed += 1
                    error = self.get_dark_msg(verify_result, host.hostname, 'ping')
                    msg = 'Verify password failed: {}'.format(error)
                    success = False
            else:
                count_failed += 1
                error = self.get_dark_msg(change_result, host.hostname, 'change_password')
                msg = 'Change password failed: {}'.format(error)
                success = False

            detail.append({
                'id': str(host.id), 'hostname': host.hostname,
                'success': success, 'msg': msg
            })

        result['count']['total'] = len(hosts)
        result['count']['success'] = count_success
        result['count']['failed'] = count_failed
        result['detail'] = sorted(detail, key=lambda x: x.get('success'))
        return result

    @staticmethod
    def is_success(result):
        if result and result.results_summary.get('contacted'):
            return True
        return False

    @staticmethod
    def get_dark_msg(result, hostname, task_name):
        try:
            dark = result.results_summary.get('dark')
            task = dark.get(hostname).get(task_name)
            unreachable = task.get('unreachable', False)
            if unreachable:
                return "Unreachable"
            else:
                return "Authentication failure"
        except Exception as e:
            logger.error('Get dark msg error: {}'.format(e))
            return ''

    def get_change_password_tasks(self, password):
        tasks = list()
        tasks.append({
            'name': 'change_password',
            'action': {
                'module': 'user',
                'args': 'name={} password={} update_password=always'.format(
                    self.username, encrypt_password(password, salt="K3mIlKK")
                ),
            }
        })
        return tasks

    def _change_password_a_asset(self, password, host):
        task_name = _('Change <{}> password to asset <{}>'.format(self.username, host))
        tasks = self.get_change_password_tasks(password)
        inventory = JMSInventory(assets=[host], run_as_admin=True)
        return self._run_task(inventory, tasks, task_name)

    def _verify_password_a_asset(self, password, host):
        task_name = _('Check <{}> password to asset <{}>'.format(self.username, host))
        tasks = const.TEST_SYSTEM_USER_CONN_TASKS
        run_as = RunAsUser(self.username, self.username, password)
        inventory = JMSInventory(assets=[host], run_as=run_as)
        return self._run_task(inventory, tasks, task_name)

    @staticmethod
    def _run_task(inventory, tasks, task_name):
        runner = AdHocRunner(inventory, options=const.TASK_OPTIONS)
        try:
            result = runner.run(
                tasks=tasks,
                pattern='all',
                play_name=task_name
            )
        except AnsibleError as e:
            logger.warn('Failed run adhoc {}, {}'.format(task_name, e))
            return None
        else:
            return result


class ChangeAssetPasswordTaskHistory(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    task = models.ForeignKey('ops.ChangeAssetPasswordTask', on_delete=models.CASCADE, verbose_name=_('Change password task'))
    _result = models.TextField(blank=True, null=True, verbose_name=_('Result'))
    is_success = models.BooleanField(default=False)
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

    @property
    def total_hosts(self):
        return self.result.get('count').get('total')

    @property
    def success_hosts(self):
        return self.result.get('count').get('success')

    @property
    def failed_hosts(self):
        return self.result.get('count').get('failed')

    @property
    def time(self):
        time = self.date_finished - self.date_start
        seconds = time.total_seconds()
        return round(seconds, 1)

    class Meta:
        ordering = ['-date_start', '-date_finished']
