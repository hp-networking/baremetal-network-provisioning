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
from neutron.api import extensions
from neutron import wsgi


EXTENDED_ATTRIBUTES_2_0 = {
    "switches": {
    }
}


class BNPSwitchController(wsgi.Controller):

    def index(self, request):
        pass

    def show(self, request, id):
        pass

    def delete(self, request, id):
        pass

    def create(self, request):
        pass


class Switch(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Switch"

    @classmethod
    def get_alias(cls):
        return "switch"

    @classmethod
    def get_description(cls):
        return ("Bare metal connected Physical switch.")

    @classmethod
    def get_updated(cls):
        return "2015-10-11T00:00:00-00:00"

    def get_resources(self):
        resources = []
        sresource = extensions.ResourceExtension("switches",
                                                 BNPSwitchController())
        resources.append(sresource)
        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return dict(EXTENDED_ATTRIBUTES_2_0.items())
        else:
            return {}
