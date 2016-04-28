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

    def _get_switch_port_dict(self):
        """Get a switch port dict."""
        rec_dict = {'id': "1234",
                    'switch_id': "test_switch1",
                    'port_name': "Tengig0/1",
                    'lag_id': "lag1234"}
        return rec_dict

    def _get_switch_lag_port_dict(self):
        """Get a switch lag port dict."""
        rec_dict = {'id': "lag1234",
                    'external_lag_id': "extlag123"}
        return rec_dict

    def _get_ironic_switch_port_map_dict(self):
        """Get a ironic switch port map dict."""
        rec_dict = {'neutron_port_id': "n1234",
                    'switch_port_id': "1234",
                    'lag_id': "lag1234",
                    'access_type': "access",
                    'segmentation_id': 100,
                    'host_id': 'ironic'}
        return rec_dict

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

    def test_add_hp_switch_lag_port(self):
        """Test add_hp_switch_lag_port method."""
        rec_dict = self._get_switch_lag_port_dict()
        db.add_hp_switch_lag_port(self.ctx, rec_dict)
        count = self.ctx.session.query(models.HPSwitchLAGPort).count()
        self.assertEqual(1, count)

    def test_add_hp_switch_port(self):
        """Test add_hp_switch_port method."""
        self._add_switch_and_lag_port()
        count = self.ctx.session.query(models.HPSwitchPort).count()
        self.assertEqual(1, count)

    def test_add_hp_ironic_switch_port_mapping(self):
        """Test hp_ironic_switch_port_mapping."""
        self._add_switch_and_lag_port()
        rec_dict = self._get_ironic_switch_port_map_dict()
        db.add_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        count = self.ctx.session.query(
            models.HPIronicSwitchPortMapping).count()
        self.assertEqual(1, count)

    def test_get_hp_switch_port_by_switchid_portname(self):
        """Test get_hp_switch_port_by_switchid_portname method."""
        self._add_switch_and_lag_port()
        result = db.get_all_hp_sw_port_by_swchid_portname(
            self.ctx,
            {'switch_id': "test_switch1", 'port_name': "Tengig0/1"})
        self.assertEqual('test_switch1', result[0].switch_id)

    def test_get_hp_switch_lag_port_by_id(self):
        """Test get_hp_switch_lag_port_by_id method."""
        self._add_switch_and_lag_port()
        result = db.get_hp_switch_lag_port_by_id(
            self.ctx, {'id': "lag1234"})
        self.assertEqual('lag1234', result.id)

    def test_get_hp_ironic_swport_map_by_id(self):
        """Test get_hp_ironic_swport_map_by_id method."""
        self._add_switch_and_lag_port()
        rec_dict = self._get_ironic_switch_port_map_dict()
        db.add_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        result = db.get_hp_ironic_swport_map_by_id(
            self.ctx, {'neutron_port_id': "n1234"})
        self.assertEqual("n1234", result[0].neutron_port_id)

    def test_update_hp_switch_lag_port(self):
        """Test update_hp_switch_lag_port method."""
        rec_dict = self._get_switch_lag_port_dict()
        db.add_hp_switch_lag_port(self.ctx, rec_dict)
        db.update_hp_switch_lag_port(
            self.ctx, {'id': "lag1234", 'external_lag_id': "extlag456"})
        result = db.get_hp_switch_lag_port_by_id(
            self.ctx, {'id': "lag1234"})
        self.assertEqual("extlag456", result.external_lag_id)

    def test_update_hp_ironic_swport_map_with_seg_id(self):
        """Test update_hp_ironic_swport_map_with_seg_id method."""
        self._add_switch_and_lag_port()
        rec_dict = self._get_ironic_switch_port_map_dict()
        db.add_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        db.update_hp_ironic_swport_map_with_seg_id(
            self.ctx, {'neutron_port_id': "n1234",
                       'access_type': "access",
                       'segmentation_id': 200,
                       'host_id': 'ironic'})
        result = db.get_hp_ironic_swport_map_by_id(
            self.ctx, {'neutron_port_id': "n1234"})
        self.assertEqual(200, result[0].segmentation_id)

    def test_get_hp_switch_port_by_id(self):
        """Test get_hp_switch_port_by_switchid_portname method."""
        self._add_switch_and_lag_port()
        result = db.get_hp_switch_port_by_id(
            self.ctx,
            {'id': "1234"})
        self.assertEqual("1234", result.id)

    def test_delete_hp_switch_port(self):
        """Test delete_hp_switch_port method."""
        self._add_switch_and_lag_port()
        sw_rec_dict = self._get_switch_port_dict()
        db.delete_hp_switch_port(self.ctx, sw_rec_dict)
        count = self.ctx.session.query(models.HPSwitchPort).count()
        self.assertEqual(count, 0)

    def test_delete_hp_ironic_switch_port_mapping(self):
        """Test delete_hp_ironic_switch_port_mapping."""
        self._add_switch_and_lag_port()
        rec_dict = self._get_ironic_switch_port_map_dict()
        db.add_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        db.delete_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        count = self.ctx.session.query(
            models.HPIronicSwitchPortMapping).count()
        self.assertEqual(count, 0)

    def test_delete_hp_switch_lag_port(self):
        """Test delete_hp_switch_lag_port method."""
        self._add_switch_and_lag_port()
        lag_dict = self._get_switch_lag_port_dict()
        db.delete_hp_switch_lag_port(self.ctx, lag_dict)
        count = self.ctx.session.query(models.HPSwitchLAGPort).count()
        self.assertEqual(count, 0)

    def _add_switch_and_lag_port(self):
        """Add entries to hpswitchports and hpswitchlagports."""
        sw_rec_dict = self._get_switch_port_dict()
        lag_dict = self._get_switch_lag_port_dict()
        db.add_hp_switch_lag_port(self.ctx, lag_dict)
        db.add_hp_switch_port(self.ctx, sw_rec_dict)

    def test_update_hp_ironic_swport_map_with_lag_id(self):
        """Test update_hp_ironic_swport_map_with_lag_id method."""
        self._add_switch_and_lag_port()
        rec_dict = self._get_ironic_switch_port_map_dict()
        lag_dict = {'id': "lag1234",
                    'external_lag_id': "1234",
                    'neutron_port_id': "n1234"}
        db.add_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        db.update_hp_ironic_swport_map_with_lag_id(
            self.ctx, lag_dict)
        result = db.get_hp_ironic_swport_map_by_id(
            self.ctx, {'neutron_port_id': "n1234"})
        self.assertEqual("lag1234", result[0].lag_id)

    def test_update_hp_swport_with_lag_id(self):
        """Test update_hp_swport_with_lag_id method."""
        self._add_switch_and_lag_port()
        lag_dict = {'id': "lag1234", 'lag_id': "1234"}
        db.update_hp_switch_ports_with_lag_id(self.ctx, lag_dict)
        result = db.get_hp_switch_port_by_id(
            self.ctx,
            {'id': "1234"})
        self.assertEqual("lag1234", result.lag_id)

    def test_get_ext_lag_id_by_id(self):
        """Test get_ext_lag_id_by_id method."""
        self._add_switch_and_lag_port()
        result = db.get_ext_lag_id_by_lag_id(
            self.ctx, {'id': "lag1234"})
        self.assertEqual('extlag123', result.external_lag_id)

# non SDN starts here
    def _get_bnp_phys_switch_dict(self):
        """Get a phy switch dict."""
        switch_dict = {'ip_address': "1.1.1.1",
                       'mac_address': "A:B:C:D",
                       'port_prov': "enable",
                       'name': "test1",
                       'vendor': "HPE",
                       'family': "test",
                       'disc_proto': 'snmpv1',
                       'disc_creds': 'creds1',
                       'prov_proto': 'snmpv1',
                       'prov_creds': 'creds2'}
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
                    'switch_port_id': "5678",
                    'switch_id': "3456"}
        return port_map

    def test_add_bnp_phys_switch(self):
        """Test add_bnp_phys_switch method."""
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        count = self.ctx.session.query(models.BNPPhysicalSwitch).count()
        self.assertEqual(1, count)

    def test_add_bnp_phys_switch_port(self):
        """Test add_bnp_phys_switch_port method."""
        port_dict = self._get_bnp_phys_switchport_dict()
        db.add_bnp_phys_switch_port(self.ctx, port_dict)
        count = self.ctx.session.query(models.BNPPhysicalSwitchPort).count()
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

    def test_update_bnp_phys_switch_status(self):
        sw_dict = self._get_bnp_phys_switch_dict()
        db.add_bnp_phys_switch(self.ctx, sw_dict)
        switches = db.get_all_bnp_phys_switches(self.ctx)
        db.update_bnp_phys_switch_status(self.ctx,
                                         switches[0]['id'],
                                         "disable")
        sw_updt = self.ctx.session.query(models.BNPPhysicalSwitch).all()
        self.assertNotEqual(sw_updt[0]['port_prov'], "disable")

    def test_update_bnp_phys_swport_status(self):
        """Test update_bnp_phys_swport_status method."""
        port_dict = self._get_bnp_phys_switchport_dict()
        db.add_bnp_phys_switch_port(self.ctx, port_dict)
        db.update_bnp_phys_swport_status(self.ctx,
                                         port_dict['switch_id'],
                                         port_dict['interface_name'],
                                         "DOWN")
        port_updt = self.ctx.session.query(models.BNPPhysicalSwitchPort).all()
        self.assertEqual(port_updt[0]['port_status'], "DOWN")

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

    def test_get_bnp_phys_switch_port_by_id(self):
        """Test get_bnp_phys_switch_port_by_id method."""
        swport = self._get_bnp_phys_switchport_dict()
        db.add_bnp_phys_switch_port(self.ctx, swport)
        port = db.get_bnp_phys_switch_ports_by_switch_id(self.ctx,
                                                         swport['switch_id'])
        new_swport = db.get_bnp_phys_switch_port_by_id(self.ctx,
                                                       port[0]['id'])
        self.assertEqual(port[0]['id'], new_swport['id'])

    def test_delete_bnp_phys_switch_ports_by_name(self):
        """Test delete_bnp_phys_switch_ports_by_name method."""
        swport_dict = self._get_bnp_phys_switchport_dict()
        db.add_bnp_phys_switch_port(self.ctx, swport_dict)
        db.delete_bnp_phys_switch_ports_by_name(self.ctx,
                                                swport_dict['switch_id'],
                                                swport_dict['interface_name'])
        count = self.ctx.session.query(models.BNPPhysicalSwitchPort).count()
        self.assertEqual(0, count)

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
        retval = db.add_bnp_snmp_cred(self.ctx, snmp_cred_dict)
        cred_val = db.get_snmp_cred_by_name(self.ctx, 'CRED1')
        self.assertEqual(retval, cred_val)

    def test_get_snmp_cred_by_id(self):
        """Test get_snmp_cred_by_id method."""
        snmp_cred_dict = self._get_snmp_cred_dict()
        retval = db.add_bnp_snmp_cred(self.ctx, snmp_cred_dict)
        cred_val = db.get_snmp_cred_by_id(self.ctx, retval['id'])
        self.assertEqual(retval, cred_val)

    def test_get_netconf_cred_by_name(self):
        """Test get_netconf_cred_by_name method."""
        netconf_cred_dict = self._get_netconf_cred_dict()
        retval = db.add_bnp_netconf_cred(self.ctx, netconf_cred_dict)
        cred_val = db.get_netconf_cred_by_name(self.ctx, 'CRED1')
        self.assertEqual(retval, cred_val)

    def test_get_netconf_cred_by_id(self):
        """Test get_netconf_cred_by_id method."""
        netconf_cred_dict = self._get_netconf_cred_dict()
        retval = db.add_bnp_netconf_cred(self.ctx, netconf_cred_dict)
        cred_val = db.get_netconf_cred_by_id(self.ctx, retval['id'])
        self.assertEqual(retval, cred_val)
