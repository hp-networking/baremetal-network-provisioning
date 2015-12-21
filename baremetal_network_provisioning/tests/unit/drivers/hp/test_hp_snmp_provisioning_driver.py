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
from baremetal_network_provisioning.common import constants as hp_const
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.db import bm_nw_provision_models as models
from baremetal_network_provisioning.drivers.hp import (
    hp_snmp_provisioning_driver as driver)

import contextlib

import mock

from neutron.plugins.ml2.common import exceptions as ml2_exc
from neutron.tests import base


class TestHPSNMPProvisioningDriver(base.BaseTestCase):

    def setUp(self):
        super(TestHPSNMPProvisioningDriver, self).setUp()
        self.driver = driver.HPSNMPProvisioningDriver()

    def test_create_port_with_switch_enabled(self):
        """Test create port for with enabled case."""
        port_dict = self._get_port_payload()
        bnp_phys_switch = models.BNPPhysicalSwitch
        bnp_phys_port = models.BNPPhysicalSwitchPort
        bnp_phys_switch.status = 'ENABLED'
        bnp_phys_by_mac = 'get_bnp_phys_switch_by_mac'
        with contextlib.nested(mock.patch.object(db, 'get_subnets_by_network',
                                                 return_value=["subnet"]),
                               mock.patch.object(db, bnp_phys_by_mac,
                                                 return_value=bnp_phys_switch),
                               mock.patch.object(db, 'get_bnp_phys_port',
                                                 return_value=bnp_phys_port)):
                    self.driver.create_port(port_dict)

    def test_create_port_with_switch_disabled(self):
        """Test create port for with disabled case."""
        port_dict = self._get_port_payload()
        bnp_phys_port = models.BNPPhysicalSwitchPort
        bnp_phys_switch = models.BNPPhysicalSwitch
        bnp_phys_switch.status = 'DISABLED'
        bnp_phys_by_mac = 'get_bnp_phys_switch_by_mac'
        with contextlib.nested(mock.patch.object(db, 'get_subnets_by_network',
                                                 return_value=["subnet"]),
                               mock.patch.object(db, bnp_phys_by_mac,
                                                 return_value=bnp_phys_switch),
                               mock.patch.object(db, 'get_bnp_phys_port',
                                                 return_value=bnp_phys_port)):
                    self.assertRaises(ml2_exc.MechanismDriverError,
                                      self.driver.create_port, port_dict)

    def test_bind_port_to_segment_success(self):
        """Test bind port to segment for success case."""
        port_dict = self._get_port_payload()
        bnp_phys_switch = models.BNPPhysicalSwitch
        bnp_phys_port = models.BNPPhysicalSwitchPort
        bnp_mappings = models.BNPSwitchPortMapping
        cred_dict = self._get_credentials_dict()
        with contextlib.nested(
            mock.patch.object(db,
                              'get_bnp_phys_switch_by_mac',
                              return_value=bnp_phys_switch),
            mock.patch.object(db,
                              'get_bnp_phys_port',
                              return_value=bnp_phys_port),
            mock.patch.object(db,
                              'get_all_bnp_swport_mappings',
                              return_value=bnp_mappings),
            mock.patch.object(self.driver,
                              '_get_credentials_dict',
                              return_value=cred_dict),
            mock.patch.object(self.driver,
                              'bind_port_to_segment',
                              return_value=hp_const.BIND_SUCCESS)):
            value = self.driver.bind_port_to_segment(port_dict)
            self.assertEqual(value, hp_const.BIND_SUCCESS)

    def test_delete_port(self):
        """Test delete neutron port."""
        bnp_mappings = models.BNPSwitchPortMapping
        bnp_phys_switch = models.BNPPhysicalSwitch
        bnp_phys_port = models.BNPPhysicalSwitchPort
        bnp_ntrn_port = models.BNPNeutronPort
        cred_dict = self._get_credentials_dict()
        with contextlib.nested(mock.patch.object(db,
                               'get_bnp_switch_port_mappings',
                                                 return_value=bnp_mappings),
                               mock.patch.object(db,
                               'get_bnp_phys_switch',
                                                 return_value=bnp_phys_switch),
                               mock.patch.object(self.driver,
                                                 '_get_credentials_dict',
                                                 return_value=cred_dict),
                               mock.patch.object(db,
                               'get_bnp_phys_switch_port_by_id',
                                                 return_value=bnp_phys_port),
                               mock.patch.object(db,
                               'get_bnp_neutron_port_by_seg_id',
                                                 return_value=bnp_ntrn_port)):
                self.driver.delete_port('321f506f-5f0d-435c-9c23-c2a11f78c3e3')

    def _get_port_payload(self):
        """Get port payload for processing requests."""
        port_dict = {'port':
                     {'segmentation_id': '1001',
                      'host_id': 'ironic',
                      'access_type': hp_const.ACCESS,
                      'switchports':
                      [{'port_id': 'Ten-GigabitEthernet1/0/35',
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
