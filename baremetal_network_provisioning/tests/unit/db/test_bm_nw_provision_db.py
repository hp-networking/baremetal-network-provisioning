# Copyright (c) 2015 OpenStack Foundation
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
from oslo_log import log as logging

from neutron import context
from neutron.tests.unit import testlib_api

from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.db import bm_nw_provision_models as models


LOG = logging.getLogger(__name__)


class NetworkProvisionDBTestCase(testlib_api.SqlTestCase):
    """Test all network provisioning db helper methods."""

    def setUp(self):
        super(NetworkProvisionDBTestCase, self).setUp()
        self.ctx = context.get_admin_context()

    def _get_snmp_cred_dict(self):
        """Get a snmp credential dict."""
        snmp_cred_dict = {
            'name': 'CRED1',
            'proto_type': 'snmpv3',
            'write_community': None,
            'security_name': 'xyz',
            'auth_protocol': 'md5',
            'auth_key': 'abcd1234',
            'priv_protocol': 'des',
            'priv_key': 'xxxxxxxx',
            'security_level': None}
        return snmp_cred_dict

    def _get_netconf_cred_dict(self):
        """Get a netconf credential dict."""
        netconf_cred_dict = {
            'name': 'CRED1',
            'proto_type': 'netconf-soap',
            'user_name': 'sdn',
            'password': 'skyline',
            'key_path': None}
        return netconf_cred_dict

# non SDN starts here
    def _get_bnp_phys_switch_dict(self):
        """Get a phy switch dict."""
        switch_dict = {'name': "test1",
                       'ip_address': "1.1.1.1",
                       'mac_address': "A:B:C:D",
                       'port_provisioning': "enable",
                       'management_protocol': "snmpv1",
                       'credentials': "creds1",
                       'validation_result': "Successful",
                       'vendor': "HPE",
                       'family': "test"}
        return switch_dict

    def _get_bnp_access_param_dict(self):
        """Get a phy switch access params dict."""
        param_dict = {'access_protocol': "snmpv3",
                      'write_community': "public",
                      'security_name': "xyz",
                      'auth_protocol': "md5",
                      'auth_key': "abc",
                      'priv_protocol': "des",
                      'priv_key': "abc",
                      'security_level': "authPriv"}
        return param_dict

    def _get_bnp_phys_switchport_dict(self):
        """Get phy switch port dict."""
        swport_dict = {'switch_id': "123",
                       'interface_name': "Tengig1/0/1",
                       'ifindex': "12345",
                       'port_status': "UP"}
        return swport_dict

    def _get_bnp_neutron_port_dict(self):
        """Get neutron port dict."""
        nport_dict = {'neutron_port_id': "1234",
                      'lag_id': "50",
                      'access_type': "access",
                      'segmentation_id': 100,
                      'bind_status': True}
        return nport_dict

    def _get_bnp_switch_port_map_dict(self):
        """Get neutron port dict."""
        port_map = {'neutron_port_id': "1234",
                    'switch_port_name': "TenGigabitEthernet",
                    'switch_id': "3456",
                    'ifindex': "1"}
        return port_map

    def test_add_bnp_phys_switch(self):
        """Test add_bnp_phys_switch method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        count = self.ctx.session.query(models.BNPPhysicalSwitch).count()
        self.assertEqual(1, count)

    def test_add_bnp_neutron_port(self):
        """Test add_bnp_neutron_port method."""
        port_dict = self._get_bnp_neutron_port_dict()
        db.add_bnp_neutron_port(self.ctx, port_dict)
        count = self.ctx.session.query(models.BNPNeutronPort).count()
        self.assertEqual(1, count)

    def test_add_bnp_switch_port_map(self):
        """Test add_bnp_switch_port_map method."""
        port_map = self._get_bnp_switch_port_map_dict()
        db.add_bnp_switch_port_map(self.ctx, port_map)
        count = self.ctx.session.query(models.BNPSwitchPortMapping).count()
        self.assertEqual(1, count)

    def test_delete_bnp_neutron_port(self):
        """Test delete_bnp_neutron_port method."""
        port_dict = self._get_bnp_neutron_port_dict()
        db.add_bnp_neutron_port(self.ctx, port_dict)
        db.delete_bnp_neutron_port(self.ctx, port_dict['neutron_port_id'])
        count = self.ctx.session.query(models.BNPNeutronPort).count()
        self.assertEqual(0, count)

    def test_delete_bnp_phys_switch(self):
        """Test delete_bnp_phys_switch method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        switch = db.get_bnp_phys_switch_by_mac(self.ctx,
                                               sw_dict['mac_address'])
        db.delete_bnp_phys_switch(self.ctx, switch['id'])
        count = self.ctx.session.query(models.BNPPhysicalSwitch).count()
        self.assertEqual(0, count)

    def test_delete_bnp_phys_switch_by_name(self):
        """Test delete_bnp_phys_switch_by_name method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        switch = db.get_bnp_phys_switch_by_name(self.ctx, sw_dict['name'])
        db.delete_bnp_phys_switch_by_name(self.ctx, switch[0]['name'])
        count = self.ctx.session.query(models.BNPPhysicalSwitch).count()
        self.assertEqual(0, count)

    def test_get_bnp_phys_switch(self):
        """Test get_bnp_phys_switch method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        sw_mac = db.get_bnp_phys_switch_by_mac(self.ctx,
                                               sw_dict['mac_address'])
        sw_ip = db.get_bnp_phys_switch_by_ip(self.ctx, sw_dict['ip_address'])
        sw_name = db.get_bnp_phys_switch_by_name(self.ctx, sw_dict['name'])
        sw = db.get_bnp_phys_switch(self.ctx, sw_mac['id'])
        self.assertEqual(sw['id'], sw_mac['id'])
        self.assertEqual(sw['id'], sw_ip['id'])
        self.assertEqual(sw['id'], sw_name[0]['id'])

    def test_get_all_bnp_phys_switches(self):
        """Test get_all__bnp_phys_switches method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        switches = db.get_all_bnp_phys_switches(self.ctx)
        self.assertEqual(1, len(switches))

    '''def test_update_bnp_phys_switch_access_params(self):
        """Tests update_bnp_phys_switch_access_params method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        param_dict = self._get_bnp_access_param_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        switches = db.get_all_bnp_phys_switches(self.ctx)
        db.update_bnp_phys_switch_access_params(self.ctx,
                                                switches[0]['id'],
                                                param_dict)
        sw_updt = self.ctx.session.query(models.BNPPhysicalSwitch).all()
        self.assertNotEqual(sw_updt[0]['access_protocol'], "snmpv3")'''

    def test_add_bnp_snmp_cred(self):
        """Test test_add_bnp_snmp_cred method."""
        snmp_cred_dict = self._get_snmp_cred_dict()
        db.add_bnp_snmp_cred(self.ctx, snmp_cred_dict)
        count = self.ctx.session.query(models.BNPSNMPCredential).count()
        self.assertEqual(1, count)

    def test_add_bnp_netconf_cred(self):
        """Test test_add_bnp_netconf_cred method."""
        netconf_cred_dict = self._get_netconf_cred_dict()
        db.add_bnp_netconf_cred(self.ctx, netconf_cred_dict)
        count = self.ctx.session.query(models.BNPNETCONFCredential).count()
        self.assertEqual(1, count)

    def test_get_snmp_cred_by_name(self):
        """Test get_snmp_cred_by_name method."""
        snmp_cred_dict = self._get_snmp_cred_dict()
        retval = [db.add_bnp_snmp_cred(self.ctx, snmp_cred_dict)]
        cred_val = db.get_snmp_cred_by_name(self.ctx, 'CRED1')
        self.assertEqual(retval, cred_val)

    def test_get_snmp_cred_by_id(self):
        """Test get_snmp_cred_by_id method."""
        snmp_cred_dict = self._get_snmp_cred_dict()
        retval = [db.add_bnp_snmp_cred(self.ctx, snmp_cred_dict)]
        cred_val = db.get_snmp_cred_by_id(self.ctx, retval[0]['id'])
        self.assertEqual(retval[0], cred_val)

    def test_get_netconf_cred_by_name(self):
        """Test get_netconf_cred_by_name method."""
        netconf_cred_dict = self._get_netconf_cred_dict()
        retval = [db.add_bnp_netconf_cred(self.ctx, netconf_cred_dict)]
        cred_val = db.get_netconf_cred_by_name(self.ctx, 'CRED1')
        self.assertEqual(retval, cred_val)

    def test_get_netconf_cred_by_id(self):
        """Test get_netconf_cred_by_id method."""
        netconf_cred_dict = self._get_netconf_cred_dict()
        retval = [db.add_bnp_netconf_cred(self.ctx, netconf_cred_dict)]
        cred_val = db.get_netconf_cred_by_id(self.ctx, retval[0]['id'])
        self.assertEqual(retval[0], cred_val)
