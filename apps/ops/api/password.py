# -*- coding: utf-8 -*-
#

from rest_framework import viewsets
from rest_framework.views import APIView, Response

from common.permissions import IsOrgAdminOrAppUser
from ..models import ChangeAssetPasswordTask
from ..serializers import BulkChangePasswordTaskSerializer
from ..tasks import bulk_change_asset_password


class BulkChangePasswordTaskViewSet(viewsets.ModelViewSet):
    serializer_class = BulkChangePasswordTaskSerializer
    permission_classes = (IsOrgAdminOrAppUser,)
    queryset = ChangeAssetPasswordTask.objects.all()


class BulkChangePasswordTaskRunApi(APIView):
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        print('pk::::::::::', pk)
        task = bulk_change_asset_password.delay(pk)
        print('task id::::::::', task.id)
        return Response({'task': task.id})
