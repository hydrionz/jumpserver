# -*- coding: utf-8 -*-
#

from rest_framework import viewsets, generics
from rest_framework.views import APIView, Response
from rest_framework.pagination import LimitOffsetPagination

from common.utils import get_object_or_none
from common.permissions import IsOrgAdminOrAppUser

from ..models import ChangeAssetPasswordTask, ChangeAssetPasswordTaskHistory
from ..serializers import (
    ChangeAssetPasswordTaskSerializer,
    ChangeAssetPasswordTaskHistoryDetailSerializer,
)
from ..tasks import (
    change_asset_password_task, change_asset_password_task_subtask
)


class ChangeAssetPasswordTaskViewSet(viewsets.ModelViewSet):
    serializer_class = ChangeAssetPasswordTaskSerializer
    permission_classes = (IsOrgAdminOrAppUser,)
    queryset = ChangeAssetPasswordTask.objects.all()


class ChangeAssetPasswordTaskRunApi(APIView):
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        task = change_asset_password_task.delay(pk)
        return Response({'task': task.id})


class ChangeAssetPasswordTaskSubtaskRunApi(APIView):
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        task = change_asset_password_task_subtask.delay(pk)
        return Response({'task': task.id})


class ChangeAssetPasswordTaskHistoryLatestDetailApi(generics.ListAPIView):
    permission_classes = (IsOrgAdminOrAppUser,)
    serializer_class = ChangeAssetPasswordTaskHistoryDetailSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ['get']

    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_object_or_none(ChangeAssetPasswordTask, pk=pk)

    def get_queryset(self):
        task = self.get_object()
        history = task.history.all()
        if not history:
            return history

        history = history.latest()
        return history.subtask_history.all().order_by('is_success')


class ChangeAssetPasswordTaskHistoryDetailApi(generics.ListAPIView):
    permission_classes = (IsOrgAdminOrAppUser,)
    serializer_class = ChangeAssetPasswordTaskHistoryDetailSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ['get']

    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_object_or_none(ChangeAssetPasswordTaskHistory, pk=pk)

    def get_queryset(self):
        history = self.get_object()
        return history.subtask_history.all().order_by('is_success')
