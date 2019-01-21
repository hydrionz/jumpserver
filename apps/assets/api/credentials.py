# -*- coding: utf-8 -*-
#


from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.translation import ugettext as _

from common.utils import get_object_or_none

from ..models import Asset
from ..credentials import get_credential_backend


class CredentialsApi(APIView):

    def get(self, request, *args, **kwargs):
        credentials = self.get_credentials()
        return Response(credentials)

    def get_credentials(self):
        asset_id = self.request.GET.get('asset_id', None)
        if asset_id is not None:
            asset = get_object_or_none(Asset, pk=asset_id)
            if asset is None:
                return []
        else:
            asset = None

        username = self.request.GET.get('username', None)
        latest = self.is_latest()
        backend = get_credential_backend()
        credentials = backend.get_credentials(
            asset=asset, username=username, latest=latest)
        return credentials

    def is_latest(self):
        latest = self.request.GET.get('latest', None)
        if latest == '1':
            return True
        else:
            return False

    def post(self, request):
        if isinstance(self.request.data, dict):
            result = self.post_credential(self.request.data)
            return Response(result)
        elif isinstance(self.request.data, list):
            result = self.post_credentials()
            return Response(result)
        else:
            return Response({'error': _('Unexpected data type')})

    def post_credentials(self):
        result = []
        for data in self.request.data:
            tmp = self.post_credential(data)
            result.append(tmp)
        return result

    def post_credential(self, data):
        username = data.get('username', None)
        if username is None:
            error = _('Username <{}> is empty.').format(username)
            return {'error': error}

        asset_id = data.get('asset_id')
        asset = get_object_or_none(Asset, pk=asset_id)
        if asset is None:
            error = _('Asset <id: {}> is not exist.').format(asset_id)
            return {'error': error}

        params = self.get_params(data, asset, username)
        backend = get_credential_backend()
        credential = backend.post_credential(**params)
        return {'msg': _('Created succeed'), 'data': credential}

    @staticmethod
    def get_params(data, asset, username):
        auth_info = {
            'password': data.get('password'),
            'public_key': data.get('public_key'),
            'private_key': data.get('private_key'),
        }
        params = {
            'name': data.get('name'),
            'asset': asset,
            'username': username,
            'comment': data.get('comment', ''),
            'auth_info': auth_info
        }
        return params


class CredentialsAuthInfoApi(APIView):

    def get(self, request, *args, **kwargs):
        credentials = self.get_credentials()
        return Response(credentials)

    def get_credentials(self):
        pk = self.kwargs.get('pk')
        backend = get_credential_backend()
        credentials = backend.get_credentials(pk=pk, include_auth=True)
        return credentials
