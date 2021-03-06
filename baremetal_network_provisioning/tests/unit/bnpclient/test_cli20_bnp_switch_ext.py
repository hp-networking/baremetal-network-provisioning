# Copyright 2016 OpenStack Foundation
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


from baremetal_network_provisioning.bnpclient.bnp_client_ext.bnpswitch import (
    _bnp_switch as bnp_switch)
from baremetal_network_provisioning.bnpclient.bnp_client_ext import shell
from baremetal_network_provisioning.tests.unit.bnpclient import test_cli20

import mock

import sys


class CLITestV20ExtensionBNPSwitchJSON(test_cli20.CLITestV20Base):

    def setUp(self):
        self._mock_extension_loading()
        super(CLITestV20ExtensionBNPSwitchJSON,
              self).setUp(plurals={'tags': 'tag'})

    def _create_patch(self, name, func=None):
        patcher = mock.patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def _mock_extension_loading(self):
        ext_pkg = ('baremetal_network_provisioning.bnpclient.bnp_client_ext'
                   '.shell')
        contrib = self._create_patch(ext_pkg + '.discover_via_entry_points')
        contrib.return_value = [("_bnp_switch",
                                 bnp_switch)]
        return contrib

    def test_ext_cmd_loaded(self):
        """Tests bnpswitch commands loaded."""
        shell.BnpShell('2.0')
        ext_cmd = {
            'switch-list':
            bnp_switch.BnpSwitchList,
            'switch-create':
            bnp_switch.BnpSwitchCreate,
            'switch-delete':
            bnp_switch.BnpSwitchDelete,
            'switch-show':
            bnp_switch.BnpSwitchShow,
            'switch-update':
            bnp_switch.BnpSwitchUpdate}
        self.assertDictContainsSubset(ext_cmd, shell.COMMANDS['2.0'])

    def test_create_bnp_switch(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchCreate(
            test_cli20.MyApp(sys.stdout), None)
        name = 'bnpSwitchName'
        ip_address = '10.0.0.1'
        vendor = 'hpe'
        myid = 'myid'
        position_names = ['name', 'ip_address', 'vendor']
        position_values = [name, ip_address, vendor]
        args = [name, ip_address, vendor]
        self._test_create_resource(
            resource, cmd, None, myid, args, position_names, position_values)

    def test_create_bnp_switch_with_all_options(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchCreate(
            test_cli20.MyApp(sys.stdout), None)
        name = 'bnpSwitchName'
        ip_address = '10.0.0.1'
        vendor = 'hpe'
        myid = 'myid'
        position_names = ['name', 'ip_address', 'vendor', 'family',
                          'disc_proto', 'disc_creds', 'prov_proto',
                          'prov_creds']
        position_values = [name, ip_address, vendor, '5900',
                           'snmpv1', 'credential1', 'snmpv2c', 'credential2']
        args = [name, ip_address, vendor, '--family', '5900', '--disc-proto',
                'snmpv1', '--disc-creds', 'credential1', '--prov-proto',
                'snmpv2c', '--prov-creds', 'credential2']
        self._test_create_resource(
            resource, cmd, None, myid, args, position_names, position_values)

    def test_update_bnp_switch_disc_proto_creds_without_discover(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchUpdate(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = ['--disc-proto', 'disc_pro', '--disc-creds', 'fake_cred', myid]
        updatefields = {'disc_proto': 'disc_pro',
                        'disc_creds': 'fake_cred', 'rediscover': False}
        self._test_update_resource(resource, cmd, myid, args, updatefields)

    def test_update_bnp_switch_disc_proto_creds_with_discover(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchUpdate(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = ['--disc-proto', 'disc_proto', '--disc-creds',
                'fake_cred', '--rediscover', myid]
        updatefields = {'disc_proto': 'disc_proto',
                        'disc_creds': 'fake_cred', 'rediscover': True}
        self._test_update_resource(resource, cmd, myid, args, updatefields)

    def test_update_bnp_switch_prov_proto_creds_without_discover(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchUpdate(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = ['--prov-proto', 'prov_proto',
                '--prov-creds', 'fake_cred', myid]
        updatefields = {'prov_proto': 'prov_proto',
                        'prov_creds': 'fake_cred', 'rediscover': False}
        self._test_update_resource(resource, cmd, myid, args, updatefields)

    def test_update_bnp_switch_prov_proto_creds_with_discover(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchUpdate(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = ['--prov-proto', 'prov_proto', '--prov-creds',
                'fake_cred', '--rediscover', myid]
        updatefields = {'prov_proto': 'prov_proto',
                        'prov_creds': 'fake_cred', 'rediscover': True}
        self._test_update_resource(resource, cmd, myid, args, updatefields)

    def test_update_bnp_switch_prov_proto_creds_enable_without_discover(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchUpdate(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = ['--prov-proto', 'prov_proto', '--prov-creds',
                'fake_cred', '--enable', 'True', myid]
        updatefields = {'prov_proto': 'prov_proto',
                        'prov_creds': 'fake_cred', 'enable': 'True',
                        'rediscover': False}
        self._test_update_resource(resource, cmd, myid, args, updatefields)

    def test_update_bnp_switch_prov_proto_creds_enable_with_discover(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchUpdate(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = ['--prov-proto', 'prov_proto', '--prov-creds',
                'fake_cred', '--enable', 'False', '--rediscover', myid]
        updatefields = {'prov_proto': 'prov_proto',
                        'prov_creds': 'fake_cred', 'enable': 'False',
                        'rediscover': True}
        self._test_update_resource(resource, cmd, myid, args, updatefields)

    def test_list_bnp_switches(self):
        resources = 'bnp_switches'
        cmd = bnp_switch.BnpSwitchList(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(resources, cmd, True)

    def test_show_bnp_switch(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchShow(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(
            resource, cmd, self.test_id, args, ['id', 'name'])

    def test_delete_bnp_switch(self):
        resource = 'bnp_switch'
        cmd = bnp_switch.BnpSwitchDelete(test_cli20.MyApp(sys.stdout), None)
        my_id = 'my-id'
        args = [my_id]
        self._test_delete_resource(resource, cmd, my_id, args)
