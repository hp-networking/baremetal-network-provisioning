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
from neutron.common import exceptions as n_exc
from neutron import wsgi

from baremetal_network_provisioning.common import constants as const
from baremetal_network_provisioning.common import validators
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.drivers import discovery_driver

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


RESOURCE_ATTRIBUTE_MAP = {
    'bnp-switches': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'ip_address': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:ip_address': None},
                       'is_visible': True, 'default': ''},
        'mac_address': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'access-parameters': {'allow_post': True, 'allow_put': True,
                              'validate': {'type:access_dict': None},
                              'is_visible': True},
        'access-protocol': {'allow_post': True, 'allow_put': True,
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

    def _check_admin(self, context):
        reason = _("Only admin can configure Bnp-switch")
        if not context.is_admin:
            raise n_exc.AdminRequired(reason=reason)

    def index(self, request, **kwargs):
        context = request.context
        switches = db.get_all_bnp_phys_switches(context)
        switches = self._switch_to_show(switches)
        switches_dict = {'bnp-switches': switches}
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
        port_status_dict = {}
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        switch_list = self._switch_to_show(switch)
        switch_dict = switch_list[0]
        bounded_ports = db.get_bnp_switch_port_map_by_switchid(
            context, id)
        if bounded_ports:
            for port in bounded_ports:
                switch_port = db.get_bnp_phys_switch_port_by_id(
                    context, port['switch_port_id'])
                port_status_dict[switch_port[
                    'interface_name']] = switch_port['port_status']
        switch_dict['ports'] = port_status_dict
        return switch_dict

    def delete(self, request, id, **kwargs):
        context = request.context
        self._check_admin(context)
        switch = db.get_bnp_phys_switch(context, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        if switch['status'] == const.SWITCH_STATUS['enable']:
            raise webob.exc.HTTPBadRequest(
                _("Disable the switch %s to delete") % id)
        db.delete_bnp_phys_switch(context, id)

    def create(self, request, **kwargs):
        context = request.context
        self._check_admin(context)
        body = validators.validate_request(request)
        key_list = ['ip_address', 'vendor',
                    'access_protocol', 'access_parameters']
        keys = body.keys()
        for key in key_list:
            if key not in keys:
                raise webob.exc.HTTPBadRequest(
                    _("Key %s not found in request body") % key)
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
        validators.validate_access_parameters(body)
        access_parameters = body.pop("access_parameters")
        switch_dict = self._create_switch_dict()
        for key, value in access_parameters.iteritems():
            body[key] = value
        switch = self._update_dict(body, switch_dict)
        bnp_switch = self._discover_switch(switch)
        if bnp_switch.get('mac_address'):
            switch['mac_address'] = bnp_switch.get('mac_address')
            switch['status'] = const.SWITCH_STATUS['enable']
        else:
            switch['status'] = const.SWITCH_STATUS['create']
        db_switch = db.add_bnp_phys_switch(context, switch)
        if bnp_switch.get('ports'):
            self._add_physical_port(context, db_switch.get('id'),
                                    bnp_switch.get('ports'))
        return dict(db_switch)

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
        phys_switch = db.get_bnp_phys_switch(context, id)
        if not phys_switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        if body.get('access_parameters', None):
            if body.get('access_protocol', None):
                protocol = body['access_protocol']
                if protocol.lower() not in const.SUPPORTED_PROTOCOLS:
                    raise webob.exc.HTTPBadRequest(
                        _("access protocol %s is not supported") % body[
                            'access_protocol'])
            else:
                protocol = phys_switch['access_protocol']
            if protocol.lower() == const.SNMP_V3:
                validators.validate_snmpv3_parameters(
                    body['access_parameters'])
            else:
                validators.validate_snmp_parameters(
                    body['access_parameters'])
            access_parameters = body.pop("access_parameters")
            for key, value in access_parameters.iteritems():
                body[key] = value
        switch_dict = self._update_dict(body, dict(phys_switch))
        switch_to_show = self._switch_to_show(switch_dict)
        switch = switch_to_show[0]
        if 'enable' in body.keys():
            if body['enable'] is False:
                if body.get('rediscover', None):
                    raise webob.exc.HTTPBadRequest(
                        _("Rediscovery of Switch %s is not supported"
                          "when Enable=False") % id)
                switch_status = const.SWITCH_STATUS['disable']
                switch['status'] = switch_status
                db.update_bnp_phys_switch_status(context,
                                                 id, switch_status)
                db.update_bnp_phys_switch_access_params(context, id,
                                                        switch_dict)
                return switch
            elif phys_switch['status'] == const.SWITCH_STATUS[
                    'enable'] and body['enable'] is True:
                raise webob.exc.HTTPBadRequest(
                    _("Disable the switch %s to update") % id)
        if phys_switch['status'] == const.SWITCH_STATUS[
           'enable'] and body.get('rediscover', None):
            raise webob.exc.HTTPBadRequest(
                _("Disable the switch %s to update") % id)
        self._discover_switch(switch_dict)
        switch_status = const.SWITCH_STATUS['enable']
        switch['status'] = switch_status
        db.update_bnp_phys_switch_status(context, id, switch_status)
        db.update_bnp_phys_switch_access_params(context, id, switch_dict)
        return switch

    def _discover_switch(self, switch):
        snmp_driver = discovery_driver.SNMPDiscoveryDriver(switch)
        bnp_switch = snmp_driver.discover_switch()
        return bnp_switch

    def _update_dict(self, body, switch_dict):
        for key in switch_dict.keys():
            if key in body.keys():
                switch_dict[key] = body[key]
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
                "for bare metal instance network provisioning")

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
