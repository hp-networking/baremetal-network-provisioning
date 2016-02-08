# Copyright 2015 OpenStack Foundation
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

import contextlib

import mock

from baremetal_network_provisioning.common import constants as hp_const
from baremetal_network_provisioning.common import exceptions
from baremetal_network_provisioning.common import snmp_client
from baremetal_network_provisioning.drivers import snmp_driver

from neutron.tests import base

from pysnmp.proto import rfc1902


class TestSnmpDriver(base.BaseTestCase):

    def setUp(self):
        super(TestSnmpDriver, self).setUp()
        self.snmp_info = {'ip_address': '00.00.00.00',
                          'access_protocol': 'snmpv1',
                          'write_community': 'public',
                          'security_name': 'user_name',
                          'auth_key': 'halo1234',
                          'priv_key': 'test1234',
                          'auth_protocol': 'md5',
                          'priv_protocol': 'des56'}
        self.driver = snmp_driver.SNMPDriver()

    def test_delete_isolation(self):
        self.port = self._get_port_payload()
        self.client = snmp_client.get_client(self.snmp_info)
        seg_id = 1001
        egress_oid = hp_const.OID_VLAN_EGRESS_PORT + '.' + str(seg_id)
        egress_byte = []
        oct_str = rfc1902.OctetString('')
        with contextlib.nested(mock.patch.object(snmp_client, 'get_client',
                                                 return_value=self.client),
                               mock.patch.object(snmp_client.SNMPClient, 'set',
                                                 return_value=None),
                               mock.patch.object(snmp_driver.SNMPDriver,
                                                 '_get_device_nibble_map',
                                                 return_value=None),
                               mock.patch.object(snmp_client.SNMPClient,
                                                 'get_bit_map_for_del',
                                                 return_value=egress_byte)):
            self.driver.delete_isolation(self.port)
            snmp_client.get_client.called
            snmp_client.SNMPClient.set.called
            snmp_driver.SNMPDriver._get_device_nibble_map.called
            snmp_client.SNMPClient.get_bit_map_for_del.called
            snmp_client.SNMPClient.set.assert_called_with(egress_oid, oct_str)

    def test_set_isolation(self):
        self.port = self._get_port_payload()
        self.client = snmp_client.get_client(self.snmp_info)
        seg_id = 1001
        egress_oid = hp_const.OID_VLAN_EGRESS_PORT + '.' + str(seg_id)
        egress_byte = []
        oct_str = rfc1902.OctetString('')
        with contextlib.nested(mock.patch.object(snmp_client, 'get_client',
                                                 return_value=self.client),
                               mock.patch.object(snmp_driver.SNMPDriver,
                                                 '_snmp_get',
                                                 return_value=None),
                               mock.patch.object(snmp_client.SNMPClient, 'set',
                                                 return_value=None),
                               mock.patch.object(snmp_driver.SNMPDriver,
                                                 '_get_device_nibble_map',
                                                 return_value=None),
                               mock.patch.object(snmp_client.SNMPClient,
                                                 'get_bit_map_for_add',
                                                 return_value=egress_byte)):
            self.driver.set_isolation(self.port)
            snmp_client.get_client.called
            snmp_driver.SNMPDriver._snmp_get.called
            snmp_client.SNMPClient.set.called
            snmp_driver.SNMPDriver._get_device_nibble_map.called
            snmp_client.SNMPClient.get_bit_map_for_add.called
            snmp_client.SNMPClient.set.assert_called_with(egress_oid, oct_str)

    def test_set_isolation_exception(self):
        self.port = self._get_port_payload()
        self.client = snmp_client.get_client(self.snmp_info)
        with contextlib.nested(
            mock.patch.object(snmp_client, 'get_client',
                              return_value=self.client),
            mock.patch.object(snmp_driver.SNMPDriver,
                              '_snmp_get',
                              return_value=None),
            mock.patch.object(snmp_client.SNMPClient, 'set',
                              side_effect=exceptions.SNMPFailure)):
            self.assertRaises(exceptions.SNMPFailure,
                              self.driver.set_isolation,
                              self.port)

    def _get_port_payload(self):
        """Get port payload for processing requests."""
        port_dict = {'port':
                     {'segmentation_id': '1001',
                      'ifindex': '1',
                      'host_id': 'ironic',
                      'access_type': hp_const.ACCESS,
                      'credentials': self._get_credentials_dict(),
                      'switchports':
                      [{'port_id': 'Ten-GigabitEthernet1/0/35',
                        'ifindex': '1',
                          'switch_id': '44:31:92:61:89:d2'}],
                      'id': '321f506f-5f0d-435c-9c23-c2a11f78c3e3',
                      'network_id': 'net-id',
                      'is_lag': False}}
        return port_dict

    def _get_credentials_dict(self):
        creds_dict = {}
        creds_dict['ip_address'] = "1.1.1.1"
        creds_dict['write_community'] = 'public'
        creds_dict['security_name'] = 'test'
        creds_dict['security_level'] = 'test'
        creds_dict['auth_protocol'] = 'md5'
        creds_dict['access_protocol'] = 'test1'
        creds_dict['auth_key'] = 'test'
        creds_dict['priv_protocol'] = 'aes'
        creds_dict['priv_key'] = 'test_priv'
        return creds_dict
