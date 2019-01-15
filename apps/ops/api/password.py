# -*- coding: utf-8 -*-
#

from rest_framework import viewsets
from rest_framework.views import APIView, Response

from common.permissions import IsOrgAdminOrAppUser

from ..models import ChangePasswordAssetTask
from ..tasks import change_password_asset_task
from ..serializers import ChangePasswordAssetTaskSerializer


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
