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
from baremetal_network_provisioning.drivers import snmp_discovery_driver
from baremetal_network_provisioning import managers

from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

hpe_opts = [
    cfg.StrOpt('disc_driver',
               default='baremetal_network_provisioning.drivers'
               '.snmp_discovery_driver.SNMPDiscoveryDriver',
               help=_("Discovery Driver to provision networks on the switches"
                       " in the cloud fabric")),
]
cfg.CONF.register_opts(hpe_opts, "ml2_hpe")

RESOURCE_ATTRIBUTE_MAP = {
    'bnp-switches': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True},
        'ip_address': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:ip_address': None},
                       'is_visible': True, 'default': ''},
        'mac_address': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'family': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:string': None},
                   'is_visible': True, 'default': ''},
        'disc-proto': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'disc-creds': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'prov-proto': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'prov-creds': {'allow_post': True, 'allow_put': True,
                       'validate': {'type:string': None},
                       'is_visible': True},
        'vendor': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:string': None},
                   'is_visible': True}
    },
}

validator_func = validators.access_parameter_validator
attributes.validators['type:access_dict'] = validator_func


class BNPSwitchController(wsgi.Controller):

    """WSGI Controller for the extension bnp-switch."""

    def __init__(self):
        self.disc_manager = managers.DiscoveryManager()

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
        auth_list = ['auth_key', 'write_community',
                     'priv_key', 'security_level']
        switch_list = []
        if isinstance(switches, list):
            for switch in switches:
                switch = dict(switch)
                for key in auth_list:
                    switch.pop(key)
                switch_list.append(switch)
        else:
            switch = dict(switches)
            for key in auth_list:
                switch.pop(key)
            switch_list.append(switch)
        return switch_list

    def show(self, request, id, **kwargs):
        context = request.context
        switch = db.get_bnp_phys_switch(context, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        try:
            snmp_drv = None
            ports_list = snmp_drv.get_ports_status()
        except Exception as e:
            LOG.error(_LE("BNP SNMP getbulk failed with exception: %s."), e)
            is_getbulk_success = False
        else:
            is_getbulk_success = True
            sw_ports = {}
            for port_dict in ports_list:
                sw_ports[port_dict['ifindex']] = port_dict['port_status']

        port_status_dict = {}
        switch_list = self._switch_to_show(switch)
        switch_dict = switch_list[0]
        bounded_ports = db.get_bnp_switch_port_map_by_switchid(
            context, id)
        if bounded_ports:
            for port in bounded_ports:
                switch_port = db.get_bnp_phys_switch_port_by_id(
                    context, port['switch_port_id'])
                if is_getbulk_success:
                    port_status_dict[switch_port['interface_name']] = (
                        const.PORT_STATUS.get(
                            str(sw_ports[switch_port['ifindex']])))
                else:
                    port_status_dict[switch_port['interface_name']] = 'UNKNOWN'
        switch_dict['ports'] = port_status_dict
        return {const.BNP_SWITCH_RESOURCE_NAME: switch_dict}

    def delete(self, request, id, **kwargs):
        context = request.context
        self._check_admin(context)
        switch = db.get_bnp_phys_switch(context, id)
        portmap = db.get_bnp_switch_port_map_by_switchid(context, id)
        if portmap:
            raise webob.exc.HTTPConflict(
                _("Switch id %s has active port mappings") % id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        if switch['port_prov'] == const.SWITCH_STATUS['enable']:
            raise webob.exc.HTTPBadRequest(
                _("Disable the switch %s to delete") % id)
        db.delete_bnp_phys_switch(context, id)

    def create(self, request, **kwargs):
        context = request.context
        self._check_admin(context)
        body = validators.validate_request(request)
        key_list = ['name', 'ip_address', 'vendor',
                    'disc_proto', 'disc_creds',
                    'prov_proto', 'prov_creds']
        keys = body.keys()
        for key in key_list:
            if key not in keys:
                raise webob.exc.HTTPBadRequest(
                    _("Key %s not found in request body") % key)
        validators.validate_attributes(keys, key_list)
        if body['vendor'] not in const.SUPPORTED_VENDORS:
            raise webob.exc.HTTPBadRequest(
                _("Switch with vendor %s is not supported") %
                body['vendor'])
        ip_address = body['ip_address']
        bnp_switch = db.get_bnp_phys_switch_by_ip(context,
                                                  ip_address)
        if bnp_switch:
            raise webob.exc.HTTPConflict(
                _("Switch with ip_address %s is already present") %
                ip_address)
        access_parameters = self._get_access_param(context, body['disc_proto'],
                                                   body['disc_creds'])
        for key, value in access_parameters.iteritems():
            body[key] = value
        bnp_switch = self._discover_switch(body)
        if bnp_switch.get('mac_address'):
            body['mac_address'] = bnp_switch.get('mac_address')
            body['port_prov'] = const.SWITCH_STATUS['enable']
        else:
            body['port_prov'] = const.SWITCH_STATUS['create']
        db_switch = db.add_bnp_phys_switch(context, body)
        if bnp_switch.get('ports'):
            self._add_physical_port(context, db_switch.get('id'),
                                    bnp_switch.get('ports'))
        return {const.BNP_SWITCH_RESOURCE_NAME: dict(db_switch)}

    def _get_access_param(self, context, proto, creds):
        access_parameters = db.get_snmp_cred_by_name(context, creds)
        return access_parameters

    def _add_physical_port(self, context, switch_id, ports):
        for port in ports:
            port['switch_id'] = switch_id
            status = const.PORT_STATUS[port['port_status']]
            port['port_status'] = status
            db.add_bnp_phys_switch_port(context, port)

    def update(self, request, id, **kwargs):
        context = request.context
        self._check_admin(context)
        body = validators.validate_request(request)
        key_list = ['access_protocol', 'access_parameters',
                    'enable', 'rediscover']
        validators.validate_attributes(body.keys(), key_list)
        validate_snmp_creds = False
        phys_switch = db.get_bnp_phys_switch(context, id)
        if not phys_switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        if body.get('access_parameters'):
            validate_snmp_creds = True
            access_parameters = body.pop("access_parameters")
            for key, value in access_parameters.iteritems():
                body[key] = value
        else:
            access_parameters = {
                'write_community': phys_switch['write_community'],
                'security_name': phys_switch['security_name'],
                'auth_protocol': phys_switch['auth_protocol'],
                'priv_protocol': phys_switch['priv_protocol'],
                'auth_key': phys_switch['auth_key'],
                'priv_key': phys_switch['priv_key'],
                'security_level': phys_switch['security_level']}
        if body.get('access_protocol'):
            validate_snmp_creds = True
            protocol = body['access_protocol']
            if protocol.lower() not in const.SUPPORTED_PROTOCOLS:
                raise webob.exc.HTTPBadRequest(
                    _("access protocol %s is not supported") % body[
                        'access_protocol'])
        else:
            protocol = phys_switch['access_protocol']
        switch_dict = self._update_dict(body, dict(phys_switch))
        switch_to_show = self._switch_to_show(switch_dict)
        switch = switch_to_show[0]
        if validate_snmp_creds:
            if protocol.lower() == const.SNMP_V3:
                validators.validate_snmpv3_parameters(access_parameters)
            else:
                validators.validate_snmp_parameters(access_parameters)
            try:
                driver = snmp_discovery_driver.SNMPDiscoveryDriver(switch_dict)
                driver.get_sys_name()
                db.update_bnp_phys_switch_access_params(context,
                                                        id, switch_dict)
            except Exception as e:
                LOG.error(_LE("Exception in validating credentials '%s' "), e)
                raise webob.exc.HTTPBadRequest(
                    _("Validation of credentials failed"))
        if body.get('enable'):
            enable = attributes.convert_to_boolean(body['enable'])
            if not enable:
                switch_status = const.SWITCH_STATUS['disable']
                db.update_bnp_phys_switch_status(context, id, switch_status)
            else:
                switch_status = const.SWITCH_STATUS['enable']
                db.update_bnp_phys_switch_status(context, id, switch_status)
            switch['status'] = switch_status
        if body.get('rediscover'):
            bnp_switch = self._discover_switch(switch_dict)
            db_switch_ports = db.get_bnp_phys_switch_ports_by_switch_id(
                context, id)
            self._update_switch_ports(context, id,
                                      bnp_switch.get('ports'),
                                      db_switch_ports)
        return switch

    def _update_switch_ports(self, context, switch_id, ports, db_switch_ports):
        port_ifname_map = {}
        db_swport_ifname_map = {}
        for port in ports:
            port_ifname_map[port['interface_name']] = const.PORT_STATUS[
                port['port_status']]
        for sw_port in db_switch_ports:
            db_swport_ifname_map[
                sw_port['interface_name']] = sw_port['port_status']
        for port_ifname in port_ifname_map.keys():
            if port_ifname in db_swport_ifname_map.keys():
                if port_ifname_map[port_ifname] != db_swport_ifname_map[
                   port_ifname]:
                    db.update_bnp_phys_swport_status(
                        context, switch_id,
                        port_ifname, port_ifname_map[port_ifname])
                port_ifname_map.pop(port_ifname)
                db_swport_ifname_map.pop(port_ifname)
            elif port_ifname not in db_swport_ifname_map.keys():
                for port in ports:
                    if port['interface_name'] == port_ifname:
                        ifindex = port['ifindex']
                        break
                phys_port = {'switch_id': switch_id,
                             'port_status': port_ifname_map[port_ifname],
                             'interface_name': port_ifname,
                             'ifindex': ifindex}
                db.add_bnp_phys_switch_port(context, phys_port)
                port_ifname_map.pop(port_ifname)
        if db_swport_ifname_map:
            for swport_ifname in db_swport_ifname_map:
                db.delete_bnp_phys_switch_ports_by_name(context, switch_id,
                                                        swport_ifname)

    def _discover_switch(self, switch):
        vendor = switch['vendor']
        protocol = switch['disc_proto']
        switch['access_protocol'] = switch['disc_proto']
        family = None
        keys = switch.keys()
        if 'family' in keys:
            family = switch['family']
        disc_driver = self._discovery_driver(protocol, vendor, family)
        bnp_switch = disc_driver.obj.discover_switch(switch)
        return bnp_switch

    def _update_dict(self, body, switch_dict):
        for key in switch_dict.keys():
            if key in body.keys():
                switch_dict[key] = body[key]
        switch_dict['access_protocol'] = body['disc_proto']
        return switch_dict

    def _create_switch_dict(self):
        switch_dict = {
            'ip_address': None,
            'mac_address': None,
            'status': None,
            'access_protocol': None,
            'vendor': None,
            'security_name': None,
            'write_community': None,
            'auth_protocol': None,
            'auth_key': None,
            'priv_protocol': None,
            'priv_key': None,
            'security_level': None}
        return switch_dict

    def _discovery_driver(self, protocol, vendor, family):
        """Get discovery driver instance based on protocol, vendor, family."""
        try:
            if const.PROTOCOL_SNMP in protocol:
                driver_key = self._driver_key(vendor, const.PROTOCOL_SNMP,
                                              family)
                driver = self.disc_manager.discovery_driver(driver_key)
            else:
                driver_key = self._driver_key(vendor, protocol,
                                              family)
                driver = self.disc_manager.discovery_driver(driver_key)
        except Exception as e:
            LOG.error(_LE("No suitable protocol driver loaded'%s' "), e)
            raise webob.exc.HTTPBadRequest(
                _("No suitable protocol driver loaded for '%s' ") % protocol)
        return driver

    def _driver_key(self, vendor, protocol, family):
        if family:
            driver_key = vendor + protocol + family
        else:
            driver_key = vendor + protocol
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
        return ("Abstraction for physical switch ports discovery"
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
