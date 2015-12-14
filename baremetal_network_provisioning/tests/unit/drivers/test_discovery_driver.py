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

from baremetal_network_provisioning.common import constants
from baremetal_network_provisioning.common import snmp_client
from baremetal_network_provisioning.drivers import discovery_driver

from neutron.tests import base


class TestDiscoveryDriver(base.BaseTestCase):

    def setUp(self):
        super(TestDiscoveryDriver, self).setUp()
        self.snmp_info = {"ip_address": '00.00.00.00',
                          'access_protocol': 'snmpv1',
                          'write_community': 'public',
                          'security_name': 'user_name',
                          'auth_key': 'halo1234',
                          'priv_key': 'test1234',
                          'auth_protocol': 'md5',
                          'priv_protocol': 'des56'}
        self.dis_driver = discovery_driver.SNMPDiscoveryDriver(self.snmp_info)

    def test__init__(self):
        with mock.patch.object(snmp_client, 'get_client',
                               return_value=None):
            discovery_driver.SNMPDiscoveryDriver(self.snmp_info)
            snmp_client.get_client.called

    def test_discover_switch(self):
        with contextlib.nested(mock.patch.object(
                               discovery_driver.SNMPDiscoveryDriver,
                               'get_mac_addr'),
                               mock.patch.object(
                               discovery_driver.SNMPDiscoveryDriver,
                               'get_ports_info',
                               return_value=None)):
            self.dis_driver.discover_switch()
            discovery_driver.SNMPDiscoveryDriver.get_mac_addr.called
            discovery_driver.SNMPDiscoveryDriver.get_ports_info.called

    def test_get_mac_addr(self):
        oid = constants.OID_MAC_ADDRESS
        with mock.patch.object(snmp_client.SNMPClient, 'get'):
            self.dis_driver.get_mac_addr()
            snmp_client.SNMPClient.get.assert_called_once_with(oid)

    def test_get_ports_info(self):
        oids = [constants.OID_PORTS,
                constants.OID_IF_INDEX,
                constants.OID_IF_TYPE,
                constants.OID_PORT_STATUS]
        with mock.patch.object(snmp_client.SNMPClient, 'get_bulk'):
            self.dis_driver.get_ports_info()
            snmp_client.SNMPClient.get_bulk.assert_called_once_with(*oids)
