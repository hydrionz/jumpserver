# -*- coding: utf-8 -*-
#

from rest_framework import viewsets
from rest_framework.views import APIView, Response

from common.permissions import IsOrgAdminOrAppUser

from ..models import ChangePasswordAssetTask
from ..serializers import ChangePasswordAssetTaskSerializer
from ..tasks import (
    change_password_asset_task,
    change_password_asset_task_subtask
)


class ChangePasswordAssetTaskViewSet(viewsets.ModelViewSet):
    serializer_class = ChangePasswordAssetTaskSerializer
    permission_classes = (IsOrgAdminOrAppUser,)
    queryset = ChangePasswordAssetTask.objects.all()


class ChangePasswordAssetTaskRunApi(APIView):
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        task = change_password_asset_task.delay(pk)
        return Response({'task': task.id})


class ChangePasswordAssetTaskSubtaskRunApi(APIView):
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        task = change_password_asset_task_subtask.delay(pk)
        return Response({'task': task.id})
