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
    hosts = models.ManyToManyField('assets.Asset')
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=128, null=True, verbose_name=_('Created by'))

    def __str__(self):
        return self.name

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
            return result
        except Exception as e:
            logger.warning(e)
            return {}
        finally:
            history.is_finished = True
            history.date_finished = timezone.now()
            history.save()

    def _run_only(self):
        """
        result = {
            'count': {
                'total': 0, 'success': 0, 'failed': 0,
            },
            'detail': {
                'failed': [], 'success': [{'hostname': 'xxx', 'msg': ''},]
            },
            'msg': 'Success',
        }
        :return: result
        """
        result = {
            'count': {'total': 0, 'success': 0, 'failed': 0},
            'detail': {'success': [], 'failed': []},
            'msg': 'Success',
        }

        count_success = count_failed = 0
        detail_success = detail_failed = []

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
                    AuthBook.create_item(self.username, password, host)
                    msg = 'Change and verify password success: {}'
                    detail_success.append({'hostname': host.hostname, 'msg': msg})
                else:
                    count_failed += 1
                    error = self.get_dark_msg(verify_result, host.hostname, 'ping')
                    msg = 'Verify password failed: {}'.format(error)
                    detail_failed.append({'hostname': host.hostname, 'msg': msg})
            else:
                count_failed += 1
                error = self.get_dark_msg(change_result, host.hostname, 'change_password')
                msg = 'Change password failed: {}'.format(error)
                detail_failed.append({'hostname': host.hostname, 'msg': msg})

        result['count']['total'] = len(hosts)
        result['count']['success'] = count_success
        result['count']['success'] = count_failed
        result['detail']['success'] = detail_success
        result['detail']['failed'] = detail_failed
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
            msg = dark.get(hostname).get(task_name).get('msg')
            return msg
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
