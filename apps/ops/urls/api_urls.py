# ~*~ coding: utf-8 ~*~
from __future__ import unicode_literals

from django.urls import path
from rest_framework.routers import DefaultRouter
from .. import api


app_name = "ops"

router = DefaultRouter()
router.register(r'tasks', api.TaskViewSet, 'task')
router.register(r'adhoc', api.AdHocViewSet, 'adhoc')
router.register(r'history', api.AdHocRunHistoryViewSet, 'history')
router.register(r'command-executions', api.CommandExecutionViewSet, 'command-execution')
router.register(r'change-password-asset-task', api.ChangePasswordAssetTaskViewSet, 'change-password-asset-task')

urlpatterns = [
    path('tasks/<uuid:pk>/run/', api.TaskRun.as_view(), name='task-run'),
    path('celery/task/<uuid:pk>/log/', api.CeleryTaskLogApi.as_view(), name='celery-task-log'),
    path('celery/task/<uuid:pk>/result/', api.CeleryResultApi.as_view(), name='celery-result'),
    path('change-password-asset-task/<uuid:pk>/run/', api.ChangePasswordAssetTaskRunApi.as_view(), name='change-password-asset-task-run'),
    path('change-password-asset-task/subtask/<uuid:pk>/run/', api.ChangePasswordAssetTaskSubtaskRunApi.as_view(), name='change-password-asset-task-subtask-run')
]

urlpatterns += router.urls
