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
router.register(r'bulk-change-password-task', api.BulkChangePasswordTaskViewSet, 'bulk-change-password-task')

urlpatterns = [
    path('tasks/<uuid:pk>/run/', api.TaskRun.as_view(), name='task-run'),
    path('celery/task/<uuid:pk>/log/', api.CeleryTaskLogApi.as_view(), name='celery-task-log'),
    path('celery/task/<uuid:pk>/result/', api.CeleryResultApi.as_view(), name='celery-result'),
    path('bulk-change-password-task/<uuid:pk>/run/', api.BulkChangePasswordTaskRunApi.as_view(), name='bulk-change-password-task-run'),
]

urlpatterns += router.urls
