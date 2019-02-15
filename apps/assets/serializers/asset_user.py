# -*- coding: utf-8 -*-
#

from rest_framework import serializers

from ..models import AuthBook


class AssetUserSerializers(serializers.ModelSerializer):
    class Meta:
        model = AuthBook
        fields = [
            'id', 'name', 'username', 'date_created', 'date_updated', 'org_id',
            'version_count'
        ]


class AssetUserAuthInfoSerializers(serializers.ModelSerializer):
    class Meta:
        model = AuthBook
        fields = [
            'password', 'public_key', 'private_key'
        ]
