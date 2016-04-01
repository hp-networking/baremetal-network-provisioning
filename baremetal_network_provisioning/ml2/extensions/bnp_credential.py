# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import webob.exc

from neutron.api import extensions
from neutron.api.v2 import attributes
from neutron.api.v2 import base
from neutron.api.v2 import resource
from neutron.i18n import _LE
from neutron import wsgi

from baremetal_network_provisioning.common import constants as const
from baremetal_network_provisioning.common import validators
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.drivers import discovery_driver

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


RESOURCE_ATTRIBUTE_MAP = {
    'bnp-credentials': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True},
        'snmpv1': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:access_dict': None},
                   'is_visible': True},
        'snmpv2c': {'allow_post': True, 'allow_put': True,
                    'validate': {'type:access_dict': None},
                    'is_visible': True},
        'snmpv3': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:access_dict': None},
                   'is_visible': True},
        'netconf-ssh': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:access_dict': None},
                        'is_visible': True},
        'netconf-soap': {'allow_post': True, 'allow_put': True,
                         'validate': {'type:access_dict': None},
                         'is_visible': True},
    },
}

validator_func = validators.access_parameter_validator
attributes.validators['type:access_dict'] = validator_func


class BNPCredentialController(wsgi.Controller):

    """WSGI Controller for the extension bnp-credential."""

    def _check_admin(self, context):
        reason = _("Only admin can configure Bnp-switch")
        if not context.is_admin:
            raise webob.exc.HTTPForbidden(reason)

    def index(self, request, **kwargs):
        print "Credential LIST"

    def show(self, request, id, **kwargs):
        print "Credential SHOW"

    def delete(self, request, id, **kwargs):
        print "Credential DELETE"

    def create(self, request, **kwargs):
        context = request.context
        self._check_admin(context)
        body = validators.validate_request(request)
        key_list = ['name', 'snmpv1', 'snmpv2c',
                    'snmpv3', 'netconf-ssh', 'netconf-soap']
        keys = body.keys()
        validators.validate_attributes(keys, key_list)
        protocol = validators.validate_access_parameters(body)
        if protocol in ['snmpv1', 'snmpv2c', 'snmpv3']:
            self._create_snmp_creds(context, body, protocol)
        else:
            self._create_netconf_creds(context, body, protocol)

    def _create_snmp_creds(self, context, body, protocol):
        name = body.get('name')
        snmp_cred = db.get_snmp_cred_by_name(context,
                                             name)
        if snmp_cred:
            raise webob.exc.HTTPConflict(
                _("SNMP Credential with %s name already present") %
                name)
        access_parameters = body.pop(protocol)
        snmp_cred_dict = self._create_snmp_cred_dict()
        for key, value in access_parameters.iteritems():
            body[key] = value
        body['proto_type'] = protocol
        snmp_cred_dict = self._update_dict(body, snmp_cred_dict)
        snmp_cred_dict = db.add_bnp_snmp_cred(context, snmp_cred_dict)

    def _create_netconf_creds(self, context, body, protocol):
        name = body.get('name')
        netconf_cred = db.get_netconf_cred_by_name(context,
                                                   name)
        if netconf_cred:
            raise webob.exc.HTTPConflict(
                _("NETCONF Credential with %s name already present") %
                name)
        access_parameters = body.pop(protocol)
        netconf_cred_dict = self._create_netconf_cred_dict()
        for key, value in access_parameters.iteritems():
            body[key] = value
        body['proto_type'] = protocol
        netconf_cred = self._update_dict(body, netconf_cred_dict)
        db_snmp_cred = db.add_bnp_netconf_cred(context, netconf_cred)


    def _create_snmp_cred_dict(self):
        snmp_cred_dict = {
            'name': None,
            'proto_type': None,
            'security_name': None,
            'write_community': None,
            'auth_protocol': None,
            'auth_key': None,
            'priv_protocol': None,
            'priv_key': None,
            'security_level': None}
        return snmp_cred_dict

    def _create_netconf_cred_dict(self):
        netconf_cred_dict = {
            'name': None,
            'proto_type': None,
            'user_name': None,
            'password': None,
            'key_path': None}
        return netconf_cred_dict

    def _update_dict(self, body, cred_dict):
        for key in cred_dict.keys():
            if key in body.keys():
                cred_dict[key] = body[key]
        return cred_dict

    def update(self, request, id, **kwargs):
        print "Credential UPDATE"


class Bnp_credential(extensions.ExtensionDescriptor):

    """API extension for Baremetal Switch Credential support."""

    @classmethod
    def get_name(cls):
        return "Bnp-Credential"

    @classmethod
    def get_alias(cls):
        return "bnp-credential"

    @classmethod
    def get_description(cls):
        return ("Abstraction for protocol credentials"
                " for bare metal instance network provisioning")

    @classmethod
    def get_updated(cls):
        return "2016-03-22T00:00:00-00:00"

    def get_resources(self):
        exts = []
        controller = resource.Resource(BNPCredentialController(),
                                       base.FAULT_MAP)
        exts.append(extensions.ResourceExtension(
            'bnp-credentials', controller))
        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}
