#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from django.conf import settings

from .vault import VaultBackend
from .db import AuthBookBackend


def get_credential_backend():
    if settings.CREDENTIAL_BACKEND_VAULT:
        return VaultBackend()
    else:
        return AuthBookBackend()


credential_backend = get_credential_backend()
