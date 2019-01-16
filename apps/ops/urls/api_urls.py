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
router.register(r'change-asset-password-task',
                api.ChangeAssetPasswordTaskViewSet, 'change-asset-password-task')

urlpatterns = [
    path('tasks/<uuid:pk>/run/', api.TaskRun.as_view(), name='task-run'),
    path('celery/task/<uuid:pk>/log/',
         api.CeleryTaskLogApi.as_view(), name='celery-task-log'),
    path('celery/task/<uuid:pk>/result/',
         api.CeleryResultApi.as_view(), name='celery-result'),

    path('change-asset-password-task/<uuid:pk>/run/',
         api.ChangeAssetPasswordTaskRunApi.as_view(),
         name='change-asset-password-task-run'),

    path('change-asset-password-task/subtask/<uuid:pk>/run/',
         api.ChangeAssetPasswordTaskSubtaskRunApi.as_view(),
         name='change-asset-password-task-subtask-run'),

    path('change-asset-password-task/<uuid:pk>/history/latest/subtask/history/',
         api.ChangeAssetPasswordTaskHistoryLatestSubtaskHistoryListApi.as_view(),
         name='change-asset-password-task-latest-subtask-history-list'),
]

urlpatterns += router.urls
