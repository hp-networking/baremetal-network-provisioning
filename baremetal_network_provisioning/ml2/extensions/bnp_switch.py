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
from baremetal_network_provisioning import managers

from oslo_log import log as logging
from oslo_utils import uuidutils

LOG = logging.getLogger(__name__)


RESOURCE_ATTRIBUTE_MAP = {
    'bnp-switches': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True},
        'ip_address': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:ip_address': None},
                       'is_visible': True, 'default': ''},
        'mac_address': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'family': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:string': None},
                   'is_visible': True, 'default': ''},
        'management_procotol': {'allow_post': True, 'allow_put': True,
                                'validate': {'type:string': None},
                                'is_visible': True},
        'credentials': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True},
        'vendor': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:string': None},
                   'is_visible': True}
    },
}

validator_func = validators.access_parameter_validator
attributes.validators['type:access_dict'] = validator_func


class BNPSwitchController(wsgi.Controller):

    """WSGI Controller for the extension bnp-switch."""

    def __init__(self):
        self.protocol_manager = managers.ProvisioningManager()

    def _check_admin(self, context):
        reason = _("Only admin can configure Bnp-switch")
        if not context.is_admin:
            raise webob.exc.HTTPForbidden(reason)

    def index(self, request, **kwargs):
        context = request.context
        filters = {}
        req_dict = dict(request.GET)
        if req_dict and req_dict.get('fields', None):
            req_dict.pop('fields')
            filters = req_dict
        switches = db.get_all_bnp_phys_switches(context, **filters)
        switches = self._switch_to_show(switches)
        switches_dict = {'bnp_switches': switches}
        return switches_dict

    def _switch_to_show(self, switches):
        switch_list = []
        if isinstance(switches, list):
            for switch in switches:
                switch = dict(switch)
                switch_list.append(switch)
        else:
            switch = dict(switches)
            switch_list.append(switch)
        return switch_list

    def show(self, request, id, **kwargs):
        context = request.context
        switch = db.get_bnp_phys_switch(context, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        switch_list = self._switch_to_show(switch)
        switch_dict = switch_list[0]
        return {const.BNP_SWITCH_RESOURCE_NAME: switch_dict}

    def delete(self, request, id, **kwargs):
        context = request.context
        self._check_admin(context)
        port_prov = None
        is_uuid = False
        if not uuidutils.is_uuid_like(id):
            switch = db.get_bnp_phys_switch_by_name(context, id)
        else:
            is_uuid = True
            switch = db.get_bnp_phys_switch(context, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        if isinstance(switch, list) and len(switch) > 1:
            raise webob.exc.HTTPConflict(
                _("Multiple switches matches found "
                  "for name %s, use an ID to be more specific.") % id)
        if isinstance(switch, list) and len(switch) == 1:
            portmap = db.get_bnp_switch_port_map_by_switchid(context,
                                                             switch[0].id)
            port_prov = switch[0].port_prov
        else:
            portmap = db.get_bnp_switch_port_map_by_switchid(context, id)
            port_prov = switch['port_provisioning']
        if portmap:
            raise webob.exc.HTTPConflict(
                _("Switch id %s has active port mappings") % id)
        if port_prov == const.SWITCH_STATUS['enable']:
            raise webob.exc.HTTPBadRequest(
                _("Disable the switch %s to delete") % id)
        if is_uuid:
            db.delete_bnp_phys_switch(context, id)
        else:
            db.delete_bnp_phys_switch_by_name(context, id)

    def create(self, request, **kwargs):
        context = request.context
        self._check_admin(context)
        body = validators.validate_request(request)
        key_list = ['name', 'ip_address', 'vendor',
                    'management_protocol', 'credentials',
                    'mac_address']
        keys = body.keys()
        for key in key_list:
            if key not in keys:
                raise webob.exc.HTTPBadRequest(
                    _("Key %s not found in request body") % key)
        validators.validate_switch_attributes(keys, key_list)
        ip_address = body['ip_address']
        if const.FAMILY not in body:
            body['family'] = ''
        bnp_switch = db.get_bnp_phys_switch_by_ip(context,
                                                  ip_address)
        if bnp_switch:
            raise webob.exc.HTTPConflict(
                _("Switch with ip_address %s is already present") %
                ip_address)
        access_parameters = self._get_access_param(context,
                                                   body['management_protocol'],
                                                   body['credentials'])
        credentials = body['credentials']
        if uuidutils.is_uuid_like(credentials):
            access_params_iterator = access_parameters.iteritems()
        else:
            access_params_iterator = access_parameters[0].iteritems()
        for key, value in access_params_iterator:
            if key == const.NAME:
                continue
            body[key] = value
        body['port_provisioning'] = const.SWITCH_STATUS['enable']
        driver_key = self._protocol_driver(body)
        try:
            if driver_key:
                mac_val = driver_key.obj.get_protocol_validation_result(body)
                if mac_val != body['mac_address']:
                    mac_str = 'Invalid MAC Actual Switch MAC is %s' % mac_val
                    result = mac_str
                else:
                    result = const.SUCCESS
                if const.DEVICE_NOT_REACHABLE in value:
                    result = const.DEVICE_NOT_REACHABLE
            else:
                result = const.NO_DRVR_FOUND
        except Exception as e:
            LOG.error(_LE(" Exception in protocol_validation_result %s "), e)
            result = const.DEVICE_NOT_REACHABLE
        body['validation_result'] = result
        db_switch = db.add_bnp_phys_switch(context, body)
        return {const.BNP_SWITCH_RESOURCE_NAME: dict(db_switch)}

    def _get_access_param(self, context, protocol, creds):
        access_parameters = None
        proto_type = None
        if const.PROTOCOL_SNMP in protocol:
            if not uuidutils.is_uuid_like(creds):
                access_parameters = db.get_snmp_cred_by_name(context, creds)
                proto_type = access_parameters[0].proto_type
            else:
                access_parameters = db.get_snmp_cred_by_id(context, creds)
                proto_type = access_parameters.proto_type
        else:
            if not uuidutils.is_uuid_like(id):
                access_parameters = db.get_netconf_cred_by_name(context, creds)
                proto_type = access_parameters[0].proto_type
            else:
                access_parameters = db.get_netconf_cred_by_id(context, creds)
                proto_type = access_parameters.proto_type
        if not access_parameters:
            raise webob.exc.HTTPNotFound(
                _("Invalid credentials %s") % creds)
        if access_parameters and proto_type == protocol:
            return access_parameters
        if access_parameters and proto_type != protocol:
            raise webob.exc.HTTPBadRequest(
                _("Invalid management_protocol %s") % protocol)

    def update(self, request, id, **kwargs):
        context = request.context
        self._check_admin(context)
        body = validators.validate_request(request)
        key_list = ['name', 'ip_address', 'vendor',
                    'management_protocol', 'credentials',
                    'mac_address', 'port_provisioning', 'validate']
        validators.validate_attributes(body.keys(), key_list)
        if uuidutils.is_uuid_like(id):
            phys_switch = db.get_bnp_phys_switch(context, id)
        else:
            phys_switch = db.get_bnp_phys_switch_name(context, id)
        if not phys_switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        switch_to_show = self._switch_to_show(phys_switch)
        switch = switch_to_show[0]
        if body.get('port_provisioning'):
            enable = body['port_provisioning']
            if enable.lower() not in const.SWITCH_STATUS.values():
                raise webob.exc.HTTPBadRequest(
                    _("Invalid port-provisioning option %s ") % enable.upper())
            db.update_bnp_phys_switch_status(context, id, enable.upper())
            switch['port_provisioning'] = enable
        return switch

    def _protocol_driver(self, switch):
        vendor = switch['vendor']
        protocol = switch['management_protocol']
        if const.FAMILY not in switch:
            switch['family'] = None
        family = switch['family']
        protocol_driver = self._protocol_driver_key(protocol, vendor, family)
        return protocol_driver

    def _protocol_driver_key(self, protocol, vendor, family):
        """Get protocol driver instance based on protocol, vendor, family."""
        try:
            driver = None
            if const.PROTOCOL_SNMP in protocol:
                driver_key = self._driver_key(vendor, const.PROTOCOL_SNMP,
                                              family)
                driver = self.protocol_manager.provisioning_driver(driver_key)
            else:
                driver_key = self._driver_key(vendor, protocol,
                                              family)
                driver = self.protocol_manager.provisioning_driver(driver_key)
        except Exception as e:
            LOG.error(_LE("No suitable protocol driver loaded '%s' "), e)
        return driver

    def _driver_key(self, vendor, protocol, family):
        if family:
            driver_key = vendor + '_' + protocol + '_' + family
        else:
            driver_key = vendor + '_' + protocol
        return driver_key


class Bnp_switch(extensions.ExtensionDescriptor):

    """API extension for Baremetal Switch support."""

    @classmethod
    def get_name(cls):
        return "Bnp-Switch"

    @classmethod
    def get_alias(cls):
        return "bnp-switch"

    @classmethod
    def get_description(cls):
        return ("Abstraction for physical switch "
                " for bare metal instance network provisioning")

    @classmethod
    def get_updated(cls):
        return "2015-10-11T00:00:00-00:00"

    def get_resources(self):
        exts = []
        controller = resource.Resource(BNPSwitchController(),
                                       base.FAULT_MAP)
        exts.append(extensions.ResourceExtension(
            'bnp-switches', controller))
        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}
