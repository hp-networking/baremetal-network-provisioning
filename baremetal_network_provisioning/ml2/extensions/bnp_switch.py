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
#    under the License.from oslo.config import cfg

from simplejson import scanner as json_scanner
import webob.exc

from neutron.api import extensions
from neutron.api.v2 import attributes
from neutron import context
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
                   'is_vidible': True}
    },
}

validator_func = validators.access_parameter_validator
attributes.validators['type:access_dict'] = validator_func


class BNPSwitchController(wsgi.Controller):

    @property
    def _dbcontext(self):
        return context.get_admin_context()

    def index(self, request):
        switches = db.get_all_bnp_phys_switches(self._dbcontext)
        switches_dict = {
            'bnp-switches': [switch.__dict__ for switch in switches]}
        return switches_dict

    def show(self, request, id):
        switch = db.get_bnp_phys_switch(self._dbcontext, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                resource="switch %s" % (id))
        switch_dict = switch.__dict__
        switch_dict['ports'] = []
        # Get a list of bounded baremetal ports
        return switch_dict

    def delete(self, request, id):
        switch = db.get_bnp_phys_switch(self._dbcontext, id)
        if not switch:
            raise webob.exc.HTTPNotFound(
                _("Switch %s does not exist") % id)
        db.delete_bnp_phys_switch(self._dbcontext, id)

    def create(self, request):
        try:
            body = request.json_body
        except json_scanner.JSONDecodeError:
            raise webob.exc.HTTPBadRequest(
                _("Invalid JSON body"))
        try:
            body = body.pop("switch")
        except KeyError:
            raise webob.exc.HTTPBadRequest(
                _("'switch' not found in request body"))
        keys = body.keys()
        key_list = ['ip_address', 'vendor',
                    'access_protocol', 'access_parameters']
        for key in key_list:
            if key not in keys:
                raise webob.exc.HTTPBadRequest(
                    _("'Key %s' not found in request body") % key)
        if body['access_protocol'].lower() not in const.SUPPORTED_PROTOCOLS:
            raise webob.exc.HTTPBadRequest(
                _("'access protocol %s' is not supported") %
                body['access_protocol'])
        access_parameters = body.pop("access_parameters")
        if body['access_protocol'].lower() == const.SNMP_V3:
            validators.validate_snmpv3_parameters(access_parameters)
        else:
            validators.validate_snmp_parameters(access_parameters)
        switch_dict = self._create_switch_dict()
        for key, value in access_parameters.iteritems():
            body[key] = value
        switch = self._update_dict(body, switch_dict)
        snmp_driver = discovery_driver.SNMPDiscoveryDriver(switch_dict)
        bnp_switch = snmp_driver.discover_switch()
        if bnp_switch.get('mac_addr'):
            switch['mac_address'] = bnp_switch.get('mac_addr')
            switch['status'] = const.Switch_status.get('enable')
        db_switch = db.add_bnp_phys_switch(self._dbcontext, switch)
        if bnp_switch.get('ports'):
            self._add_physical_port(db_switch.get('id'),
                                    bnp_switch.get('ports'))
        return switch

    def _add_physical_port(self, switch_id, ports):
        for port in ports:
            port['switch_id'] = switch_id
            status = const.Port_status.get(port['port_status'])
            port['port_status'] = status
            db.add_bnp_phys_switch_port(self._dbcontext, port)

    def update(self, request, id):
        try:
            body = request.json_body
        except json_scanner.JSONDecodeError:
            raise webob.exc.HTTPBadRequest(
                _("Invalid JSON body"))
        try:
            body = body.pop("switch")
        except KeyError:
            raise webob.exc.HTTPBadRequest(
                _("'switch' not found in request body"))
        access_parameters = body.pop("access_parameters")
        for key, value in access_parameters.iteritems():
            body[key] = value
        phys_switch = db.get_bnp_phys_switch(self._dbcontext, id)
        switch_dict = self._update_dict(body, phys_switch.__dict__)
        if body['access_protocol'] in [const.SNMP_V1, const.SNMP_V2C]:
            switch = db.update_bnp_phys_switch_snmpv2(self._dbcontext,
                                                      id, switch_dict)
        else:
            switch = db.update_bnp_phys_switch_snmpv3(self._dbcontext,
                                                      id, switch_dict)
        return switch

    def _update_dict(self, body, switch_dict):
        for key in switch_dict.keys():
            if key in body.keys():
                switch_dict[key] = body[key]
        return switch_dict

    def _create_switch_dict(self):
        switch_dict = {
            'ip_address': None,
            'mac_address': None,
            'status': const.Switch_status.get('create'),
            'access_protocol': None,
            'vendor': None,
            'write_community': None,
            'security_name': None,
            'auth_protocol': None,
            'auth_key': None,
            'priv_protocol': None,
            'priv_key': None,
            'security_level': None}
        return switch_dict


class Bnp_switch(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Bnp-Switch"

    @classmethod
    def get_alias(cls):
        return "bnp-switch"

    @classmethod
    def get_description(cls):
        return ("Bare metal connected Physical switch.")

    @classmethod
    def get_updated(cls):
        return "2015-10-11T00:00:00-00:00"

    def get_resources(self):
        resources = []
        sresource = extensions.ResourceExtension("bnp-switches",
                                                 BNPSwitchController())
        resources.append(sresource)
        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}
