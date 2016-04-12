# Copyright 2015 OpenStack Foundation.
# All Rights Reserved
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
#

from neutronclient.common import extension
from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20

from baremetal_network_provisioning.common import constants as const


class BnpSwitch(extension.NeutronClientExtension):
    resource = const.BNP_SWITCH_RESOURCE_NAME
    resource_plural = '%ses' % resource
    path = 'bnp-switches'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']


class BnpSwitchCreate(extension.ClientExtensionCreate, BnpSwitch):
    """Create Physical Switch information."""
    shell_command = 'switch-create'

    def add_known_arguments(self, parser):

        parser.add_argument('name', metavar='NAME',
                            help=_('Name of the physical switch.'))
        parser.add_argument('ip_address', metavar='IP_ADDRESS',
                            help=_('IP address of the physical switch.'))
        parser.add_argument('vendor', metavar='VENDOR',
                            help=_('Vendor of the physical switch.'))
        parser.add_argument('--family',
                            metavar='FAMILY',
                            help=_('Family of the physical switch.'))
        parser.add_argument('--disc-proto',
                            metavar='DISCOVERY_PROTOCOL',
                            help=_('Discovery protocol of the physical'
                                   ' switch.'))
        parser.add_argument('--disc-creds',
                            metavar='DISCOVERY_CREDENTIALS',
                            help=_('Discovery credential of the physical'
                                   ' switch.'))
        parser.add_argument('--prov-proto',
                            metavar='PROVISIONING_PROTOCOL',
                            help=_('Provisioning protocol of the physical'
                                   ' switch.'))
        parser.add_argument('--prov-creds',
                            metavar='PROVISIONING_CREDENTIALS',
                            help=_('Provisioning credential of the physical'
                                   ' switch.'))

    def args2body(self, parsed_args):

        body = {
            const.BNP_SWITCH_RESOURCE_NAME: {
                'name': parsed_args.name,
                'ip_address': parsed_args.ip_address,
                'vendor': parsed_args.vendor}}
        neutronV20.update_dict(parsed_args, body[
                               const.BNP_SWITCH_RESOURCE_NAME], [
                               'family', 'disc_proto', 'disc_creds',
                               'prov_proto', 'prov_creds'])
        return body


class BnpSwitchList(extension.ClientExtensionList, BnpSwitch):
    """List all physical switch information."""

    shell_command = 'switch-list'
    allow_names = False
    list_columns = ['id', 'name', 'vendor', 'family',
                    'ip_address', 'port_prov', 'disc_proto', 'prov_proto']
    pagination_support = True
    sorting_support = True


class BnpSwitchShow(extension.ClientExtensionShow, BnpSwitch):
    """Show the physical switch information."""

    shell_command = 'switch-show'
    allow_names = False


class BnpSwitchDelete(extension.ClientExtensionDelete, BnpSwitch):
    """Delete the physical switch."""

    shell_command = 'switch-delete'
    allow_names = False


class BnpSwitchUpdate(extension.ClientExtensionUpdate, BnpSwitch):
    """Update the physical switch information."""

    shell_command = 'switch-update'
    allow_names = False

    def add_known_arguments(self, parser):

        parser.add_argument('--disc-proto', metavar='DISCOVERY_PROTOCOL',
                            help=_('Discovery protocol of the physical'
                                   ' switch.'))
        parser.add_argument('--disc-creds', metavar='DISCOVERY_CREDENTIAL',
                            help=_('Discovery credential of the physical'
                                   ' switch.'))
        parser.add_argument('--prov-proto', metavar='PROVISIONING_PROTOCOL',
                            help=_('Provisioning protocol of the physical'
                                   ' switch.'))
        parser.add_argument('--prov-creds', metavar='PROVISIONING_CREDENTIALS',
                            help=_('Provisioning credentials of the physical'
                                   ' switch.'))
        utils.add_boolean_argument(parser, '--enable',
                                   help=_('Enable or Disable the switch.'))
        parser.add_argument('--rediscover', action='store_true',
                            help=_('Trigger rediscovery of the physical'
                                   ' switch.'))

    def args2body(self, parsed_args):

        body = {const.BNP_SWITCH_RESOURCE_NAME: {}}
        neutronV20.update_dict(parsed_args, body[
                               const.BNP_SWITCH_RESOURCE_NAME], [
                               'disc_proto', 'disc_creds', 'prov_proto',
                               'prov_creds', 'enable', 'rediscover'])
        return body
