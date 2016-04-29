# Copyright (c) 2016 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webob.exc

from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import resource
from neutron import wsgi

from baremetal_network_provisioning.db import bm_nw_provision_db as db

RESOURCE_ATTRIBUTE_MAP = {
    'bnp-switch-ports': {
        'switch_name': {'allow_post': False, 'allow_put': False,
                        'is_visible': True},
        'neutron_port_id': {'allow_post': False, 'allow_put': False,
                            'is_visible': True},
        'switch_port_name': {'allow_post': False, 'allow_put': False,
                             'is_visible': True},
        'segmentation_id': {'allow_post': False, 'allow_put': False,
                            'is_visible': True},
        'lag_id': {'allow_post': False, 'allow_put': False,
                   'is_visible': True},
        'bind_status': {'allow_post': False, 'allow_put': False,
                        'is_visible': True},
        'access_type': {'allow_post': False, 'allow_put': False,
                        'is_visible': True}

    },
}


class BNPSwitchPortController(wsgi.Controller):

    """WSGI Controller for the extension bnp-switch-port."""

    def index(self, request, **kwargs):
        context = request.context
        req_dict = dict(request.GET)
        if req_dict and req_dict.get('fields', None):
            req_dict.pop('fields')
        filters = req_dict
        port_maps = db.get_all_bnp_switch_port_maps(context, **filters)
        port_list = []
        for port_map in port_maps:
            port_dict = {'neutron_port_id': port_map[0],
                         'switch_port_name': port_map[1],
                         'lag_id': port_map[2],
                         'segmentation_id': str(port_map[3]),
                         'access_type': port_map[4],
                         'bind_status': str(port_map[5]),
                         'switch_name': port_map[6]}
            port_list.append(port_dict)
        return {'bnp_switch_ports': port_list}

    def create(self, request, **kwargs):
        raise webob.exc.HTTPBadRequest(
            _("This operation is not allowed"))

    def show(self, request, id, **kwargs):
        raise webob.exc.HTTPBadRequest(
            _("This operation is not allowed"))

    def delete(self, request, id, **kwargs):
        raise webob.exc.HTTPBadRequest(
            _("This operation is not allowed"))

    def update(self, request, id, **kwargs):
        raise webob.exc.HTTPBadRequest(
            _("This operation is not allowed"))


class Bnp_switchport(extensions.ExtensionDescriptor):

    """API extension for Baremetal Switch port support."""

    @classmethod
    def get_name(cls):
        return "Baremetal Switch Ports"

    @classmethod
    def get_alias(cls):
        return "bnp-switch-port"

    @classmethod
    def get_description(cls):
        return ("Abstraction for physical switch ports"
                "which are mapped to neutron port bindings"
                "for a given switch")

    @classmethod
    def get_updated(cls):
        return "2016-05-26T00:00:00-00:00"

    def get_resources(self):
        exts = []
        controller = resource.Resource(BNPSwitchPortController(),
                                       base.FAULT_MAP)
        exts.append(extensions.ResourceExtension(
            'bnp-switch-ports', controller))
        return exts

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}
