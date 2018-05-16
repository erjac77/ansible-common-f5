#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016-2018, Eric Jacob <erjac77@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Ansible Common Utility Module for F5 BIG-IP
"""

import time

from ansible_common_f5.base import AnsibleF5Error, F5BaseClient, F5NamedBaseObject, F5UnnamedBaseObject

# Make sure the f5-sdk is installed on the host
try:
    from f5.bigip import ManagementRoot as BigIpMgmtRoot

    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


class F5BigIpClient(F5BaseClient):
    """F5 BIG-IP client

    It provides an interface to a single F5 BIG-IP system.
    """

    def __init__(self, **kwargs):
        if not HAS_F5SDK:
            raise AnsibleF5Error("The python f5-sdk module is required. Try 'pip install f5-sdk'.")
        self.provider = kwargs.get('provider', None)

    @property
    def mgmt_root(self):
        err = None

        for x in range(3):
            try:
                return BigIpMgmtRoot(
                    self.provider['f5_hostname'],
                    self.provider['f5_username'],
                    self.provider['f5_password'],
                    port=self.provider['f5_port'],
                    verify=self.provider['f5_verify'],
                    token='tmos'
                )
            except Exception as exc:
                err = exc
                time.sleep(10)

        err_msg = 'Unable to connect to {0} on port {1}.'.format(self.provider['f5_hostname'], self.provider['f5_port'])
        if err is not None:
            err_msg += ' The error message was "{0}".'.format(str(err))
        raise AnsibleF5Error(err_msg)

    @property
    def _system_version(self):
        version = self.mgmt_root.tm.sys.version.load()
        return version.entries['https://localhost/mgmt/tm/sys/version/0']['nestedStats']['entries'][
            'Version']['description']


class F5BigIpNamedObject(F5NamedBaseObject):
    """Base class for all F5 BIG-IP named objects"""

    @property
    def _api(self):
        return F5BigIpClient(provider=self._provider).mgmt_root


class F5BigIpUnnamedObject(F5UnnamedBaseObject):
    """Base class for all F5 BIG-IP unnamed objects"""

    @property
    def _api(self):
        return F5BigIpClient(provider=self._provider).mgmt_root
