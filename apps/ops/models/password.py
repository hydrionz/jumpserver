# -*- coding: utf-8 -*-
#


import json
import uuid
import time
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from orgs.mixins import OrgModelMixin
from assets.tasks import clean_hosts, const
from assets.models import AuthBook
from assets.models.utils import private_key_validator
from ..inventory import JMSInventory
from ..ansible import AdHocRunner, AnsibleError
from common.utils import (
    get_logger, get_signer, random_password_gen, encrypt_password
)

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


class ChangePasswordAssetTask(OrgModelMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    username = models.CharField(max_length=128, verbose_name=_('Username'))
    hosts = models.ManyToManyField('assets.Asset', verbose_name=_('Host'))
    comment = models.TextField(verbose_name=_('Comment'), blank=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Date created'))
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=128, blank=True, verbose_name=_('Created by'))

    @property
    def hosts_name(self):
        return [host.hostname for host in self.hosts.all().order_by('hostname')]

    @property
    def run_times(self):
        return self.history.all().count()

    @property
    def date_last_run(self):
        return self.history.all().latest().date_created

    def run(self):
        history = ChangePasswordAssetTaskHistory.objects.create(task=self)
        history.task_snapshot = json.dumps(self._to_attr_json())
        time_start = time.time()
        try:
            history.date_start = timezone.now()
            is_success = self._run_only(history)
            history.is_success = is_success
        except Exception as e:
            history.is_success = False
            logger.warning(e)
        finally:
            history.timedelta = time.time() - time_start
            history.date_finished = timezone.now()
            history.save()

    def _is_can_run(self, hosts=None):
        if self.username == 'root':
            reason = 'Change <{}> password is not allowed'.format(self.username)
            logger.debug(reason)
            return False, reason

        if not hosts:
            reason = 'No host needs to change password'
            logger.debug(reason)
            return False, reason

        return True, '-'

    def _run_only(self, history):
        hosts = clean_hosts(self.hosts.all())
        ok, reason = self._is_can_run(hosts)
        if not ok:
            return False

        for host in hosts:
            self.run_subtask(host, history)
        return True

    def run_subtask(self, host, task_history=None):
        history, created = ChangePasswordOneAssetTaskHistory.objects.\
            get_or_create(task_history=task_history, asset=host)
        time_start = time.time()
        try:
            history.date_start = timezone.now()
            is_success, reason, password = self._run_subtask_only(host)
            history.is_success = is_success
            history.reason = reason
            history.password = password
        except Exception as e:
            logger.warning(e)
            history.reason = 'Subtask exception'
            history.is_success = False
        finally:
            history.timedelta = time.time() - time_start
            history.date_finished = timezone.now()
            history.save()

    def _run_subtask_only(self, host):
        """
        :return: is_success, reason, password
        """
        hosts = clean_hosts([host])
        ok, reason = self._is_can_run(hosts)
        if not ok:
            return False, reason, None

        password = random_password_gen()
        is_success, reason = self.change_password(password, host)
        return is_success, reason, password

    def change_password(self, password, host):
        result = self._change_password(password, host)

        if self.result_success(result):
            is_success, reason = self.verify_password(password, host)
        else:
            is_success = False
            msg = self.get_result_failed_msg(result, host.hostname,
                                             'change_password')
            reason = '{}:{}'.format('Change password', msg)

        return is_success, reason

    def verify_password(self, password, host):
        result = self._verify_password(password, host)

        if self.result_success(result):
            is_success = True
            reason = '-'
            AuthBook.create_item(self.username, password, host)
        else:
            is_success = False
            msg = self.get_result_failed_msg(result, host.hostname, 'ping')
            reason = '{}:{}'.format('Verify password', msg)

        return is_success, reason

    def _change_password(self, password, host):
        task_name = _('Change <{}> password of asset <{}>'.format(self.username,
                                                                  host))
        tasks = self.get_change_password_task(password)
        inventory = JMSInventory(assets=[host], run_as_admin=True)
        return self._run_task(inventory, tasks, task_name)

    def _verify_password(self, password, host):
        task_name = _('Check <{}> password of asset <{}>'.format(self.username,
                                                                 host))
        tasks = const.TEST_SYSTEM_USER_CONN_TASKS
        run_as = RunAsUser(self.username, self.username, password)
        inventory = JMSInventory(assets=[host], run_as=run_as)
        return self._run_task(inventory, tasks, task_name)

    @staticmethod
    def _run_task(inventory, tasks, task_name):
        runner = AdHocRunner(inventory, options=const.TASK_OPTIONS)
        try:
            result = runner.run(tasks=tasks, pattern='all', play_name=task_name)
        except AnsibleError as e:
            logger.warning('Failed run adhoc {}, {}'.format(task_name, e))
            return None
        else:
            return result

    @staticmethod
    def result_success(result):
        if result and result.results_summary.get('contacted'):
            return True
        return False

    @staticmethod
    def get_result_failed_msg(result, hostname, task_name):
        try:
            msg = result.results_summary.get('dark'). \
                get(hostname).get(task_name).get('msg')
        except Exception as e:
            logger.debug(e)
            return 'Unknown'
        else:
            return msg

    def get_change_password_task(self, password):
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

    def _to_attr_json(self):
        return {
            'name': self.name,
            'username': self.username,
            'hosts': [host.hostname for host in self.hosts.all()],
            'comment': self.comment,
            'date_created': str(self.date_created),
            'date_updated': str(self.date_updated),
            'create_by': self.created_by,
            'org_id': self.org_id
        }

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [('org_id', 'name')]


class ChangePasswordAssetTaskHistoryModelMixin(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    is_success = models.BooleanField(default=False, verbose_name=_('Is success'))
    timedelta = models.FloatField(default=0.0, verbose_name=_('Time'), null=True)
    date_start = models.DateTimeField(db_index=True, default=timezone.now, verbose_name=_("Date start"))
    date_finished = models.DateTimeField(blank=True, null=True, verbose_name=_('End time'))
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Date created'))
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ChangePasswordAssetTaskHistory(ChangePasswordAssetTaskHistoryModelMixin):
    task = models.ForeignKey(ChangePasswordAssetTask, related_name='history', on_delete=models.CASCADE)
    task_snapshot = models.TextField(verbose_name=_("Task snapshot"))

    class Meta:
        get_latest_by = 'date_updated'


class ChangePasswordOneAssetTaskHistory(ChangePasswordAssetTaskHistoryModelMixin):
    task_history = models.ForeignKey(ChangePasswordAssetTaskHistory, related_name='subtask_history', on_delete=models.CASCADE)
    asset = models.ForeignKey('assets.Asset', related_name='change_password_asset_history', on_delete=models.CASCADE)
    _password = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Password'))
    _public_key = models.TextField(max_length=4096, blank=True, verbose_name=_('SSH public key'))
    _private_key = models.TextField(max_length=4096, blank=True, null=True, verbose_name=_('SSH private key'), validators=[private_key_validator, ])
    _old_password = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Old password'))
    reason = models.CharField(max_length=128, default='-', blank=True, verbose_name=_('Reason'))

    @property
    def old_password(self):
        if self._old_password:
            return signer.unsign(self._old_password)
        else:
            return None

    @property
    def password(self):
        if self._password:
            return signer.unsign(self._password)
        else:
            return None

    @password.setter
    def password(self, password_raw):
        self._old_password = self._password
        self._password = signer.sign(password_raw)

    def run(self):
        return self.task_history.task.run_subtask(self.asset, self.task_history)

