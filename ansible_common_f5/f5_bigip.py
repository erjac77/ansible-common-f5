#!/usr/bin/python
#
# Copyright 2016-2017, Eric Jacob <erjac77@gmail.com>
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

from ansible_common_f5.f5_base import *

### F5 BIG-IP classes ###

class F5BigIpNamedObject(F5NamedBaseObject):
    """Base class for all F5 BIG-IP named objects"""

    def get_f5_product_name(self):
        return 'bigip'

class F5BigIpUnnamedObject(F5UnnamedBaseObject):
    """Base class for all F5 BIG-IP unnamed objects"""

    def get_f5_product_name(self):
        return 'bigip'

### Ansible F5 BIG-IP module classes ###

class AnsibleModuleF5BigIpNamedObject(AnsibleModuleF5NamedObject):
    pass

class AnsibleModuleF5BigIpUnnamedObject(AnsibleModuleF5UnnamedObject):
    pass