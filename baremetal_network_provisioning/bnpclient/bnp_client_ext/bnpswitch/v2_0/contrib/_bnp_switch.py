# Copyright 2015 Rackspace Hosting Inc.
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

from baremetal_network_provisioning.common import constants as const

meta = ('write_community=write,security_name=name,'
        'auth_protocol=auth,priv_protocol=priv,'
        'auth_key=key,priv_key=key,security_level=level1')


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
        parser.add_argument(
            'ip_address',
            help=_('IP Address of the Physical Switch'))
        parser.add_argument(
            'vendor',
            help=_('Vendor of the Physical Switch'))
        parser.add_argument(
            'access_protocol',
            help=_('Protocol for accessing the Physical Switch'))
        parser.add_argument(
            '--access_parameters',
            metavar=meta, action='append', dest='access_parameters',
            type=utils.str2dict,
            help=_('Protocol access credentials of the Physical Switch'))

    def args2body(self, parsed_args):

        body = {
            const.BNP_SWITCH_RESOURCE_NAME: {
                'ip_address': parsed_args.ip_address,
                'vendor': parsed_args.vendor,
                'access_protocol': parsed_args.access_protocol}}
        if parsed_args.access_parameters:
            parameters = parsed_args.access_parameters[0]
            write_community = parameters.get('write_community')
            security_name = parameters.get('security_name')
            auth_key = parameters.get('auth_key')
            priv_key = parameters.get('priv_key')
            auth_protocol = parameters.get('auth_protocol')
            priv_protocol = parameters.get('priv_protocol')
            access_parameters = {'write_community': write_community,
                                 'security_name': security_name,
                                 'auth_key': auth_key,
                                 'priv_key': priv_key,
                                 'auth_protocol': auth_protocol,
                                 'priv_protocol': priv_protocol}
            body['bnp_switch']['access_parameters'] = access_parameters
        return body


class BnpSwitchList(extension.ClientExtensionList, BnpSwitch):
    """List all Physical Switch information."""

    shell_command = 'switch-list'
    allow_names = False
    list_columns = ['id', 'mac_address', 'ip_address', 'vendor', 'status']
    pagination_support = True
    sorting_support = True


class BnpSwitchShow(extension.ClientExtensionShow, BnpSwitch):
    """Show the Physical Switch information."""

    shell_command = 'switch-show'
    allow_names = False


class BnpSwitchDelete(extension.ClientExtensionDelete, BnpSwitch):
    """Delete the Physical Switch."""

    shell_command = 'switch-delete'
    allow_names = False


class BnpSwitchUpdate(extension.ClientExtensionUpdate, BnpSwitch):
    """Update the Physical Switch information."""

    shell_command = 'switch-update'
    allow_names = False

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--access_protocol',
            help=_('Protocol with which the Switch will be connected'))
        parser.add_argument(
            '--access_parameters',
            metavar=meta, action='append', dest='access_parameters',
            type=utils.str2dict,
            help=_('SNMP Credentials of the Switch'))
        utils.add_boolean_argument(
            parser, '--enable',
            help=_('Enable or Disable the switch'))
        parser.add_argument(
            '--rediscover', action='store_true',
            help=_('Trigger rediscovery of the Switch'))

    def args2body(self, parsed_args):

        body = {const.BNP_SWITCH_RESOURCE_NAME: {}}
        if parsed_args.enable:
            body[const.BNP_SWITCH_RESOURCE_NAME][
                'enable'] = parsed_args.enable
        if parsed_args.rediscover:
            body[const.BNP_SWITCH_RESOURCE_NAME][
                'rediscover'] = parsed_args.rediscover
        if parsed_args.access_protocol:
            body[const.BNP_SWITCH_RESOURCE_NAME][
                'access_protocol'] = parsed_args.access_protocol
        if parsed_args.access_parameters:
            parameters = parsed_args.access_parameters[0]
            write_community = parameters.get('write_community')
            security_name = parameters.get('security_name')
            auth_key = parameters.get('auth_key')
            priv_key = parameters.get('priv_key')
            auth_protocol = parameters.get('auth_protocol')
            priv_protocol = parameters.get('priv_protocol')
            access_parameters = {'write_community': write_community,
                                 'security_name': security_name,
                                 'auth_key': auth_key,
                                 'priv_key': priv_key,
                                 'auth_protocol': auth_protocol,
                                 'priv_protocol': priv_protocol}
            body[const.BNP_SWITCH_RESOURCE_NAME][
                'access_parameters'] = access_parameters
        return body
