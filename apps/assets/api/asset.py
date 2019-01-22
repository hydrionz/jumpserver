# -*- coding: utf-8 -*-
#

import random

from rest_framework import generics
from rest_framework.response import Response
from rest_framework_bulk import BulkModelViewSet
from rest_framework_bulk import ListBulkCreateUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from common.mixins import IDInFilterMixin
from common.utils import get_logger, get_object_or_none
from common.permissions import IsOrgAdmin, IsOrgAdminOrAppUser
from ..models import Asset, AdminUser, Node
from .. import serializers
from ..tasks import update_asset_hardware_info_manual, \
    test_asset_connectivity_manual
from ..utils import LabelFilter
from .credentials import credential_backend


logger = get_logger(__file__)
__all__ = [
    'AssetViewSet', 'AssetListUpdateApi',
    'AssetRefreshHardwareApi', 'AssetAdminUserTestApi',
    'AssetGatewayApi', 'AssetAssetUserApi', 'AssetAssetUserAuthInfoApi',
]


class AssetViewSet(IDInFilterMixin, LabelFilter, BulkModelViewSet):
    """
    API endpoint that allows Asset to be viewed or edited.
    """
    filter_fields = ("hostname", "ip")
    search_fields = filter_fields
    ordering_fields = ("hostname", "ip", "port", "cpu_cores")
    queryset = Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsOrgAdminOrAppUser,)

    def filter_node(self, queryset):
        node_id = self.request.query_params.get("node_id")
        if not node_id:
            return queryset

        node = get_object_or_404(Node, id=node_id)
        show_current_asset = self.request.query_params.get("show_current_asset") in ('1', 'true')

        if node.is_root() and show_current_asset:
            queryset = queryset.filter(
                Q(nodes=node_id) | Q(nodes__isnull=True)
            )
        elif node.is_root() and not show_current_asset:
            pass
        elif not node.is_root() and show_current_asset:
            queryset = queryset.filter(nodes=node)
        else:
            queryset = queryset.filter(
                nodes__key__regex='^{}(:[0-9]+)*$'.format(node.key),
            )
        return queryset

    def filter_admin_user_id(self, queryset):
        admin_user_id = self.request.query_params.get('admin_user_id')
        if not admin_user_id:
            return queryset
        admin_user = get_object_or_404(AdminUser, id=admin_user_id)
        queryset = queryset.filter(admin_user=admin_user)
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = self.filter_node(queryset)
        queryset = self.filter_admin_user_id(queryset)
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset().distinct()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class AssetListUpdateApi(IDInFilterMixin, ListBulkCreateUpdateDestroyAPIView):
    """
    Asset bulk update api
    """
    queryset = Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    permission_classes = (IsOrgAdmin,)


class AssetRefreshHardwareApi(generics.RetrieveAPIView):
    """
    Refresh asset hardware info
    """
    queryset = Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    permission_classes = (IsOrgAdmin,)

    def retrieve(self, request, *args, **kwargs):
        asset_id = kwargs.get('pk')
        asset = get_object_or_404(Asset, pk=asset_id)
        task = update_asset_hardware_info_manual.delay(asset)
        return Response({"task": task.id})


class AssetAdminUserTestApi(generics.RetrieveAPIView):
    """
    Test asset admin user assets_connectivity
    """
    queryset = Asset.objects.all()
    permission_classes = (IsOrgAdmin,)
    serializer_class = serializers.TaskIDSerializer

    def retrieve(self, request, *args, **kwargs):
        asset_id = kwargs.get('pk')
        asset = get_object_or_404(Asset, pk=asset_id)
        task = test_asset_connectivity_manual.delay(asset)
        return Response({"task": task.id})


class AssetGatewayApi(generics.RetrieveAPIView):
    queryset = Asset.objects.all()
    permission_classes = (IsOrgAdminOrAppUser,)
    serializer_class = serializers.GatewayWithAuthSerializer

    def retrieve(self, request, *args, **kwargs):
        asset_id = kwargs.get('pk')
        asset = get_object_or_404(Asset, pk=asset_id)

        if asset.domain and \
                asset.domain.gateways.filter(protocol=asset.protocol).exists():
            gateway = random.choice(asset.domain.gateways.filter(protocol=asset.protocol))
            serializer = serializers.GatewayWithAuthSerializer(instance=gateway)
            return Response(serializer.data)
        else:
            return Response({"msg": "Not have gateway"}, status=404)


def get_asset_users(asset, include_auth=False):
    users = credential_backend.get_credentials(asset=asset, latest=True,
                                               include_auth=include_auth)

    # system users #

    # sorted
    system_users = asset.systemuser_set.all().order_by('-priority',
                                                       '-date_updated')
    # group by username
    system_users_dict = {}
    for su in system_users:
        system_users_dict[su.username] = system_users_dict.get(su.username) \
                                         or []
        system_users_dict[su.username].append(su)
    # get first
    system_users = []
    for _, su in system_users_dict.items():
        if su:
            system_users.append(su[0])

    # system user append credential if username not exist
    for su in system_users:
        if su.username == asset.admin_user.username:
            su = asset.admin_user

        if su.username not in [user.get('username') for user in users]:
            data = su._to_json(include_auth=include_auth)
            data.update({'asset_id': asset.id})
            users.append(data)

    return users


def get_asset_user_auth_info(asset, username):
    users = get_asset_users(asset, include_auth=True)
    for user in users:
        if user.get('username') == username:
            return user
    return {}


class AssetAssetUserApi(APIView):
    """
    返回当前资产的所有可登录用户信息（管理用户、系统用户、credentials用户<AuthBook,Vault>）
    """
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, *args, **kwargs):
        asset = get_object_or_none(Asset, pk=self.kwargs.get('pk'))
        if asset is None:
            return {'error': 'Asset is not exist.'}

        users = get_asset_users(asset)
        return Response(users)


class AssetAssetUserAuthInfoApi(APIView):
    """
    返回当前资产下用户名为username的用户认证信息
    """
    permission_classes = (IsOrgAdminOrAppUser,)

    def get(self, request, *args, **kwargs):
        username = self.kwargs.get('username')
        asset = get_object_or_none(Asset, pk=self.kwargs.get('pk'))
        if asset is None:
            return {'error': 'Asset <id: {}> is not exist.'}

        user_auth_info = get_asset_user_auth_info(asset, username)
        return Response(user_auth_info)
