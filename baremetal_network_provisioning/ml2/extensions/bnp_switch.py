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
        switch = db.get_bnp_phys_switch(context, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        portmap = db.get_bnp_switch_port_map_by_switchid(context, id)
        if portmap:
            raise webob.exc.HTTPConflict(
                _("Switch id %s has active port mappings") % id)
        if switch['port_provisioning'] == const.SWITCH_STATUS['enable']:
            raise webob.exc.HTTPBadRequest(
                _("Disable the switch %s to delete") % id)
        db.delete_bnp_phys_switch(context, id)

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
        body['port_provisioning'] = const.SWITCH_STATUS['enable']
        result = self.validate_protocol(access_parameters, credentials, body)
        body['validation_result'] = result
        db_switch = db.add_bnp_phys_switch(context, body)
        return {const.BNP_SWITCH_RESOURCE_NAME: dict(db_switch)}

    def validate_protocol(self, access_parameters, credentials, body):
        if uuidutils.is_uuid_like(credentials):
            access_params_iterator = access_parameters.iteritems()
        else:
            access_params_iterator = access_parameters[0].iteritems()
        for key, value in access_params_iterator:
            if key == const.NAME:
                continue
            body[key] = value
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
        return result

    def _get_access_param(self, context, protocol, creds):
        if const.PROTOCOL_SNMP in protocol:
            if not uuidutils.is_uuid_like(creds):
                access_parameters = db.get_snmp_cred_by_name(context, creds)
            else:
                access_parameters = db.get_snmp_cred_by_id(context, creds)
        else:
            if not uuidutils.is_uuid_like(creds):
                access_parameters = db.get_netconf_cred_by_name(context, creds)
            else:
                access_parameters = db.get_netconf_cred_by_id(context, creds)
        if not access_parameters:
            raise webob.exc.HTTPBadRequest(
                _("Credentials not found "
                  "for  %s ") % creds)
        if isinstance(access_parameters, list):
            proto_type = access_parameters[0].proto_type
        else:
            proto_type = access_parameters.proto_type
        if access_parameters and proto_type == protocol:
            return access_parameters
        if isinstance(access_parameters, list) and len(access_parameters) > 1:
            raise webob.exc.HTTPBadRequest(
                _("Multiple credentials matches found "
                  "for name %s, use an ID to be more specific.") % id)
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
        phys_switch = db.get_bnp_phys_switch(context, id)
        update_list = []
        if not phys_switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        switch_to_show = self._switch_to_show(phys_switch)
        switch = switch_to_show[0]
        if body.get('ip_address'):
            ip = body['ip_address']
            bnp_switch = db.get_bnp_phys_switch_by_ip(context, ip)
            if bnp_switch:
                raise webob.exc.HTTPConflict(
                    _("Switch with ip_address %s is already present") %
                    ip)
            else:
                ip_dict = {'ip_address': ip}
                update_list.append(ip_dict)
                switch['ip_address'] = ip
        if body.get('port_provisioning'):
            enable = body['port_provisioning']
            if enable.lower() not in const.SWITCH_STATUS.values():
                raise webob.exc.HTTPBadRequest(
                    _("Invalid port-provisioning option %s ") % enable.lower())
            prov_dict = {'port_provisioning': enable.lower()}
            update_list.append(prov_dict)
            switch['port_provisioning'] = enable
        if body.get('name'):
            name = body['name']
            name_dict = {'name': name}
            update_list.append(name_dict)
            switch['name'] = name
        if body.get('vendor'):
            vendor = body['vendor']
            vendor_dict = {'vendor': vendor}
            update_list.append(vendor_dict)
            switch['vendor'] = vendor
        if body.get('management_protocol') or body.get('credentials'):
            if body.get('management_protocol') and body.get('credentials'):
                proto = body['management_protocol']
                cred = body['credentials']
                self._get_access_param(context,
                                       proto,
                                       cred)
                proto_dict = {'management_protocol': proto}
                cred_dict = {'credentials': cred}
                update_list.append(proto_dict)
                update_list.append(cred_dict)
                switch['management_protocol'] = proto
                switch['credentials'] = cred
            if body.get('management_protocol') and not body.get('credentials'):
                proto = body['management_protocol']
                self._get_access_param(context,
                                       proto,
                                       switch['credentials'])
                proto_dict = {'management_protocol': proto}
                update_list.append(proto_dict)
                switch['management_protocol'] = proto
            if body.get('credentials') and not body.get('management_protocol'):
                cred = body['credentials']
                self._get_access_param(context,
                                       switch['management_protocol'],
                                       cred)
                cred_dict = {'credentials': cred}
                update_list.append(cred_dict)
                switch['credentials'] = cred
        if body.get('mac_address') or body.get('validate'):
            body['vendor'] = switch['vendor']
            body['management_protocol'] = switch['management_protocol']
            body['family'] = switch['family']
            sw_proto = switch['management_protocol']
            sw_cred = switch['credentials']
            if body.get('mac_address') and body.get('validate'):
                body['ip_address'] = switch['ip_address']
                access_parameters = self._get_access_param(context,
                                                           sw_proto,
                                                           sw_cred)
                result = self.validate_protocol(access_parameters,
                                                switch['credentials'], body)
                val_dict = {'validation_result': result}
                mac_dict = {'mac_address': body['mac_address']}
                update_list.append(val_dict)
                update_list.append(mac_dict)
                switch['validation_result'] = result
                switch['mac_address'] = body['mac_address']
            if body.get('validate') and not body.get('mac_address'):
                body['ip_address'] = switch['ip_address']
                body['mac_address'] = switch['mac_address']
                access_parameters = self._get_access_param(context,
                                                           sw_proto,
                                                           sw_cred)
                result = self.validate_protocol(access_parameters,
                                                switch['credentials'], body)
                val_dict = {'validation_result': result}
                update_list.append(val_dict)
                switch['validation_result'] = result
            if body.get('mac_address') and not body.get('validate'):
                body['ip_address'] = switch['ip_address']
                access_parameters = self._get_access_param(context,
                                                           sw_proto,
                                                           sw_cred)
                result = self.validate_protocol(access_parameters,
                                                switch['credentials'], body)
                val_dict = {'validation_result': result}
                mac_dict = {'mac_address': body['mac_address']}
                update_list.append(val_dict)
                update_list.append(mac_dict)
                switch['mac_address'] = body['mac_address']
                switch['validation_result'] = result
        for update_dict in update_list:
            if update_dict:
                db.update_bnp_phy_switch(context, id, update_dict)
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
