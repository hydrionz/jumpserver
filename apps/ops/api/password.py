# -*- coding: utf-8 -*-
#

from rest_framework import viewsets

from common.permissions import IsOrgAdminOrAppUser

from ..models import ChangePasswordAssetTask
from ..serializers import ChangePasswordAssetTaskSerializer


class ChangePasswordAssetTaskViewSet(viewsets.ModelViewSet):
    serializer_class = ChangePasswordAssetTaskSerializer
    permission_classes = (IsOrgAdminOrAppUser,)
    queryset = ChangePasswordAssetTask.objects.all()
