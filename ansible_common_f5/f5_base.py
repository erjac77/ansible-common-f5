#!/usr/bin/python
#
# Copyright 2016, Eric Jacob <erjac77@gmail.com>
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

"""Ansible Common Utility Module for F5 systems

This module provides utility classes and helper functions to ease the interaction between Ansible and F5 systems.
"""

import re
from abc import ABCMeta, abstractmethod
from six import iterkeys

import requests
from requests.exceptions import HTTPError
# Disable Insecure Request Warning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Make sure the f5-sdk is installed on the host
HAS_F5SDK = True
HAS_F5SDK_ERROR = None
try:
    from f5.bigip import ManagementRoot as BigIpMgmtRoot
    from f5.bigiq import ManagementRoot as BigIqMgmtRoot
    from f5.iworkflow import ManagementRoot as iWfMgmtRoot
except ImportError as e:
    HAS_F5SDK = False
    HAS_F5SDK_ERROR = str(e)

from ansible.module_utils.basic import *

# Common choices
F5_ACTIVATION_CHOICES = ['enabled', 'disabled']
F5_POLAR_CHOICES = ['yes', 'no']
F5_SEVERITY_CHOICES = ['alert', 'crit', 'debug', 'emerg', 'err', 'info', 'notice', 'warning']
F5_STATE_CHOICES = ['present', 'absent']
F5_SWITCH_CHOICES = ['on', 'off']

# Common arguments
F5_COMMON_ARGS = dict(
    f5_hostname=dict(type='str', required=True),
    f5_username=dict(type='str', required=True),
    f5_password=dict(type='str', required=True, no_log=True),
    f5_port=dict(type='int', default=443)
)
F5_COMMON_OBJ_ARGS = dict(
    state=dict(type='str', choices=F5_STATE_CHOICES, default='present')
)
F5_COMMON_NAMED_OBJ_ARGS = dict(
    name=dict(type='str', required=True),
    partition=dict(type='str', default='Common'),
    sub_path=dict(type='str')
)

### F5 Classes ###

class AnsibleF5Error(Exception):
    pass

class F5Client(object):
    """Base abstract class for all F5 clients

    It provides an interface to a single F5 system.
    """

    def __init__(self):
        if not HAS_F5SDK:
            raise AnsibleF5Error("The python f5-sdk module is required. Try 'pip install f5-sdk'.")

    def get_mgmt_root(self, f5_product_name, **kwargs):
        if f5_product_name == 'bigip':
            # Connect to BIG-IP
            return BigIpMgmtRoot(
                kwargs['f5_hostname'],
                kwargs['f5_username'],
                kwargs['f5_password'],
                port=kwargs['f5_port']
            )
        elif f5_product_name == 'bigiq':
            # Connect to BIG-IQ
            return BigIqMgmtRoot(
                kwargs['f5_hostname'],
                kwargs['f5_username'],
                kwargs['f5_password'],
                port=kwargs['f5_port']
            )
        elif f5_product_name == 'iworkflow':
            # Connect to iWorkflow
            return iWfMgmtRoot(
                kwargs['f5_hostname'],
                kwargs['f5_username'],
                kwargs['f5_password'],
                port=kwargs['f5_port']
            )

class F5BaseObject(object):
    """Base abstract class for all F5 objects

    It represents a F5 resource configurable by Ansible.
    """

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        """Prepare the parameters needed by this module."""
        super(F5BaseObject, self).__init__()

        # Required params
        self.required_create_params = set()
        self.required_load_params = set()
        self.required_update_params = set()

        # Store the params that are sent to the module
        self.params = kwargs

        # The state of the object
        self.state = self.params['state']
        # The check mode ("dry-run") option
        self.check_mode = self.params['check_mode']

        # Set Management Root
        self.mgmt_root = F5Client().get_mgmt_root(self.get_f5_product_name(), **kwargs)

        # Set CRUD methods
        self.set_crud_methods()

        # Remove BIG-IP and Ansible params
        self.params.pop('f5_hostname', None)
        self.params.pop('f5_username', None)
        self.params.pop('f5_password', None)
        self.params.pop('f5_port', None)
        self.params.pop('state', None)
        self.params.pop('check_mode', None)

        # Translate conflictual params (eg 'state')
        for k, v in self.params['tr'].iteritems():
            if k in self.params:
                self.params[v] = self.params[k]
                self.params.pop(k, None)
        self.params.pop('tr', None)

        # Change Snake to Camel naming convention
        self.params = change_dict_naming_convention(self.params, snake_to_camel)

        # The object
        self.obj = None

    @abstractmethod
    def set_crud_methods(self):
        """Get the CRUD methods for this BIG-IP object.

        Any class inheriting from F5BaseObject should implement and override this method.
        """
        pass

    @abstractmethod
    def get_f5_product_name(self):
        """Set the F5 product name.

        Any class inheriting from F5BaseObject should implement and override this method.
        """
        pass

    def _check_create_params(self):
        """Params given to _create should satisfy required params."""
        check = _missing_required_params(self.required_create_params, self.params)
        if check:
            raise AnsibleF5Error("Missing required create params: %s" % check)

    def _check_load_params(self):
        """Params given to load should satisfy required params."""
        check = _missing_required_params(self.required_load_params, self.params)
        if check:
            raise AnsibleF5Error("Missing required load params: %s" % check)

    def _check_update_params(self):
        """Params given to update should satisfy required params."""
        check = _missing_required_params(self.required_update_params, self.params)
        if check:
            raise AnsibleF5Error("Missing required update params: %s" % check)

    def _read(self):
        """Implement this by overriding it in a subclass of 'F5NamedBaseObject' or 'F5UnnamedBaseObject'."""
        raise AnsibleF5Error("Only F5NamedBaseObject and F5UnnamedBaseObject support 'read/load'.")

    def _create(self):
        """Implement this by overriding it in a subclass of 'F5NamedBaseObject'."""
        raise AnsibleF5Error("Only F5NamedBaseObject supports 'create'.")

    def _delete(self):
        """Implement this by overriding it in a subclass of 'F5NamedBaseObject'."""
        raise AnsibleF5Error("Only F5NamedBaseObject supports 'delete'.")

    def _update(self):
        """Update the object on the BIG-IP system."""
        # Load the object
        self.obj = self._read()

        # Check params
        self._check_update_params()

        changed = False
        cparams = dict() # The params that have changed

        # Determine if some params have changed
        for key, val in self.params.iteritems():
            new_val = format_value(val)

            if new_val is not None:
                cur_val = None

                if hasattr(self.obj, key):
                    attr = getattr(self.obj, key)
                    cur_val = format_value(attr)

                # If it's a list/set...
                if isinstance(new_val, set):
                    if cur_val is None:
                        cur_val = set()
                    if self.state == "present":
                        new_list = list(cur_val | new_val)
                        if len(new_list) > len(cur_val):
                            cparams[key] = new_list
                    if self.state == "absent":
                        new_list = list(cur_val - new_val)
                        if len(new_list) < len(cur_val):
                            cparams[key] = new_list
                # If not...
                else:
                    if new_val != cur_val:
                        cparams[key] = new_val

        # If changed params, update the object
        if cparams:
            changed = True

            if self.check_mode:
                return changed

            self.obj.update(**cparams)
            self.obj.refresh()

        return changed

    def flush(self):
        """Send the buffered object to the BIG-IP system, depending upon the state of the object."""
        result = dict()

        if self.state == "present":
            has_changed = self._present()
        elif self.state == "absent":
            has_changed = self._absent()

        result.update(dict(changed=has_changed))
        return result

class F5NamedBaseObject(F5BaseObject):
    """Base abstract class for all F5 named objects"""

    def _exists(self):
        """Check for the existence of the named object on the BIG-IP system."""
        try:
            return self.methods['exists'](**self._get_resource_id_from_params())
        except HTTPError as err:
            return False

    def _read(self):
        """Load an already configured object from the BIG-IP system."""
        self._check_load_params()
        return self.methods['read'](**self._get_resource_id_from_params())

    def _create(self):
        """Create the object on the BIG-IP system."""
        # Remove empty params
        params = dict((k, v) for k, v in self.params.iteritems() if v is not None)

        # Check params
        self._check_create_params()

        if self.check_mode:
            return True

        # Create the object
        self.methods['create'](**params)

        # Make sure it is created
        if self._exists():
            return True
        else:
            raise AnsibleF5Error("Failed to create the object.")

        return True

    def _delete(self):
        """Delete the object on the BIG-IP system."""
        # Load the object
        self.obj = self._read()

        if self.check_mode:
            return True

        # Delete the object
        self.obj._delete()

        # Make sure it is gone
        if self._exists():
            raise AnsibleF5Error("Failed to delete the object.")

        return True

    def _present(self):
        has_changed = False

        if self._exists():
            has_changed = self._update()
        else:
            has_changed = self._create()

        return has_changed

    def _absent(self):
        has_changed = False

        if self._exists():
            has_changed = self._delete()

        return has_changed

    def _strip_partition(self, name):
        partition_prefix = "/{0}/".format(self.params['partition'])
        return str(name.replace(partition_prefix, ''))

    def _get_resource_id_from_params(self):
        res_id_args = { 'name': self.params['name'] }

        if 'partition' in self.params and self.params['partition'] is not None:
            res_id_args.update({ 'partition': self.params['partition'] })
        if 'subPath' in self.params and self.params['subPath'] is not None:
            res_id_args.update({ 'subPath': self.params['subPath'] })

        return res_id_args

    def _get_resource_id_from_path(self, path):
        res_id_args = {}
        path_segments = path.split('/')

        if len(path_segments) == 1:
            res_id_args.update({ 'name': path_segments[0] })
            if 'partition' in self.params and self.params['partition'] is not None:
                res_id_args.update({ 'partition': self.params['partition'] })
        elif len(path_segments) == 2:
            res_id_args.update({ 'partition': path_segments[0] })
            res_id_args.update({ 'name': path_segments[1] })
        elif len(path_segments) == 3:
            res_id_args.update({ 'partition': path_segments[0] })
            res_id_args.update({ 'subPath': path_segments[1] })
            res_id_args.update({ 'name': path_segments[2] })
        else:
            raise AnsibleF5Error("Invalid resource id.")

        return res_id_args

class F5UnnamedBaseObject(F5BaseObject):
    """Base abstract class for all F5 unnamed objects

    These objects do not support create or delete.
    """

    def _read(self):
        """Load an already configured object from the BIG-IP system."""
        self._check_load_params()
        return self.methods['read']()

    def _create(self):
        raise AnsibleF5Error("%s does not support create" % self.__class__.__name__)

    def _delete(self):
        raise AnsibleF5Error("%s does not support delete" % self.__class__.__name__)

    def _present(self):
        return self._update()

    def _absent(self):
        return self._update()

### Ansible F5 module classes ###

class AnsibleModuleF5NamedObject(AnsibleModule):
    def __init__(self, argument_spec, supports_check_mode, mutually_exclusive=[]):
        merged_arg_spec = dict()
        merged_arg_spec.update(F5_COMMON_ARGS)
        merged_arg_spec.update(F5_COMMON_OBJ_ARGS)
        merged_arg_spec.update(F5_COMMON_NAMED_OBJ_ARGS)
        if argument_spec:
            merged_arg_spec.update(argument_spec)

        super(AnsibleModuleF5NamedObject, self).__init__(argument_spec=merged_arg_spec, supports_check_mode=supports_check_mode, mutually_exclusive=mutually_exclusive)

class AnsibleModuleF5UnnamedObject(AnsibleModule):
    def __init__(self, argument_spec, supports_check_mode, mutually_exclusive=[]):
        merged_arg_spec = dict()
        merged_arg_spec.update(F5_COMMON_ARGS)
        merged_arg_spec.update(F5_COMMON_OBJ_ARGS)
        if argument_spec:
            merged_arg_spec.update(argument_spec)

        super(AnsibleModuleF5UnnamedObject, self).__init__(argument_spec=merged_arg_spec, supports_check_mode=supports_check_mode, mutually_exclusive=mutually_exclusive)

### Helper functions ###

def _missing_required_params(rqset, params):
    key_set = set(list(iterkeys(params)))
    required_minus_received = rqset - key_set

    if required_minus_received != set():
        return list(required_minus_received)

def camel_to_snake(name):
    camel_pat = re.compile(r'([A-Z])')
    return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)

def snake_to_camel(name):
    under_pat = re.compile(r'_([a-z])')
    return under_pat.sub(lambda x: x.group(1).upper(), name)

def change_dict_naming_convention(d, convert_fn):
    new = {}

    for k, v in d.iteritems():
        new_v = v
        new[convert_fn(k)] = new_v

    return new

def format_value(value):
    formatted_value = value

    if isinstance(value, basestring):
        formatted_value = value.strip()
    if isinstance(value, list):
        formatted_value = set(value)

    return formatted_value