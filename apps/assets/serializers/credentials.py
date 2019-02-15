# -*- coding: utf-8 -*-
#

from django.utils.translation import ugettext as _
from rest_framework import serializers

from ..models import AuthBook
from ..backends.credentials import credential_backend

__all__ = [
    'CredentialSerializer', 'CredentialAuthInfoSerializer'
]


class CredentialSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=256, allow_blank=True,  allow_null=True, write_only=True,
        required=False, help_text=_('Password')
    )
    public_key = serializers.CharField(
        max_length=4096, allow_blank=True, allow_null=True, write_only=True,
        required=False, help_text=_('Public key')
    )
    private_key = serializers.CharField(
        max_length=4096, allow_blank=True, allow_null=True, write_only=True,
        required=False, help_text=_('Private key')
    )

    class Meta:
        model = AuthBook
        exclude = ('_password', '_public_key', '_private_key')
        read_only_fields = (
            'id', 'date_created', 'date_updated', 'created_by', 'is_latest',
            'version_count'
        )
        extra_kwargs = {
            'username': {'required': True}
        }

    def create(self, validated_data):
        instance = credential_backend.create(
            name=validated_data['name'],
            asset=validated_data['asset'],
            username=validated_data['username'],
            password=validated_data.get('password', None),
            public_key=validated_data.get('public_key', None),
            private_key=validated_data.get('private_key', None),
            comment=validated_data.get('comment', ''),
            org_id=validated_data.get('org_id', ''),
        )
        return instance


class CredentialAuthInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthBook
        fields = [
            "id", "name", "username", "asset",
            "password", "private_key", "public_key"
        ]
