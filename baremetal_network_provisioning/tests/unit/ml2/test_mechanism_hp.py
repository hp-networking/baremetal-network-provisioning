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
from baremetal_network_provisioning.ml2 import (hp_network_provisioning_driver
                                                as np_drv)
from baremetal_network_provisioning.ml2 import mechanism_hp as hp_mech

import contextlib

import mock
from oslo_config import cfg

from neutron.extensions import portbindings
from neutron.tests import base
CONF = cfg.CONF


class TestHPMechDriver(base.BaseTestCase):
    """Test class for mech driver."""

    def setUp(self):
        super(TestHPMechDriver, self).setUp()
        self.driver = hp_mech.HPMechanismDriver()
        self.np_driver = np_drv.HPNetworkProvisioningDriver()
        self.driver.initialize()
        self.driver._load_drivers()

    def _get_port_context(self, tenant_id, net_id, vm_id, network):
        """Get port context."""
        port = {'device_id': vm_id,
                'device_owner': 'compute',
                'binding:host_id': 'ubuntu1',
                'name': 'test-port',
                'tenant_id': tenant_id,
                'id': 123456,
                'network_id': net_id,
                'binding:profile':
                {'local_link_information': [{'switch_id': '11:22:33:44:55:66',
                                             'port_id': 'Tengig0/1'}]},
                'binding:vnic_type': 'baremetal',
                'admin_state_up': True,
                'bind_requested': True
                }
        return FakePortContext(port, port, network)

    def _get_network_context(self, tenant_id, net_id, seg_id, shared):
        """Get network context."""
        network = {'id': net_id,
                   'tenant_id': tenant_id,
                   'name': 'test-net',
                   'shared': shared}
        network_segments = [{'segmentation_id': seg_id}]
        return FakeNetworkContext(network, network_segments, network)

    def _get_port_dict(self):
        """Get port dict."""
        port_dict = {'port':
                     {'segmentation_id': 1001,
                      'access_type': hp_const.ACCESS,
                      'switchports':
                      [{'port_id': 'Tengig0/1',
                          'switch_id': '11:22:33:44:55:66'}],
                      'id': 123456,
                      'is_lag': False}}
        return port_dict

    def test_create_port_precommit(self):
        """Test create_port_precommit method."""
        fake_port_dict = mock.Mock()
        fake_context = mock.Mock()
        with contextlib.nested(
            mock.patch.object(hp_mech.HPMechanismDriver,
                              '_is_port_of_interest',
                              return_value=True),
            mock.patch.object(hp_mech.HPMechanismDriver,
                              '_construct_port',
                              return_value=fake_port_dict),
            mock.patch.object(np_drv.HPNetworkProvisioningDriver,
                              'create_port',
                              return_value=None)
        ) as (is_port, cons_port, c_port):
            self.driver.create_port_precommit(fake_context)
            is_port.assert_called_with(fake_context)
            cons_port.assert_called_with(fake_context)
            c_port.assert_called_with(fake_port_dict)

    def test_delete_port_precommit(self):
        """Test delete_port_precommit method."""
        tenant_id = 'ten-1'
        network_id = 'net1-id'
        segmentation_id = 1001
        vm_id = 'vm1'
        network_context = self._get_network_context(tenant_id,
                                                    network_id,
                                                    segmentation_id,
                                                    False)

        port_context = self._get_port_context(tenant_id,
                                              network_id,
                                              vm_id,
                                              network_context)
        port_id = port_context.current['id']
        with contextlib.nested(
            mock.patch.object(hp_mech.HPMechanismDriver,
                              '_get_vnic_type',
                              return_value=portbindings.VNIC_BAREMETAL),
            mock.patch.object(np_drv.HPNetworkProvisioningDriver,
                              'delete_port',
                              return_value=None)
        ) as (vnic_type, d_port):
            self.driver.delete_port_precommit(port_context)
            vnic_type.assert_called_with(port_context)
            d_port.assert_called_with(port_id)

    def test_update_port_precommit(self):
        """Test update_port_precommit method."""
        tenant_id = 'ten-1'
        network_id = 'net1-id'
        segmentation_id = 1001
        vm_id = 'vm1'
        fake_port_dict = self._get_port_dict()
        network_context = self._get_network_context(tenant_id,
                                                    network_id,
                                                    segmentation_id,
                                                    False)

        port_context = self._get_port_context(tenant_id,
                                              network_id,
                                              vm_id,
                                              network_context)
        with contextlib.nested(
            mock.patch.object(hp_mech.HPMechanismDriver,
                              '_construct_port',
                              return_value=fake_port_dict),
            mock.patch.object(np_drv.HPNetworkProvisioningDriver,
                              'update_port',
                              return_value=None)
        ) as (cons_port, u_port):
            self.driver.update_port_precommit(port_context)
            cons_port.assert_called_with(port_context)
            u_port.assert_called_with(fake_port_dict)

    def test__construct_port(self):
        """Test _construct_port method."""
        tenant_id = 'ten-1'
        network_id = 'net1-id'
        segmentation_id = 1001
        vm_id = 'vm1'
        fake_port_dict = self._get_port_dict()
        network_context = self._get_network_context(tenant_id,
                                                    network_id,
                                                    segmentation_id,
                                                    False)

        port_context = self._get_port_context(tenant_id,
                                              network_id,
                                              vm_id,
                                              network_context)
        port_dict = self.driver._construct_port(port_context, segmentation_id)
        self.assertEqual(port_dict, fake_port_dict)

    def test__get_binding_profile(self):
        """Test _get_binding_profile method."""
        tenant_id = 'ten-1'
        network_id = 'net1-id'
        segmentation_id = 1001
        vm_id = 'vm1'
        network_context = self._get_network_context(tenant_id,
                                                    network_id,
                                                    segmentation_id,
                                                    False)

        port_context = self._get_port_context(tenant_id,
                                              network_id,
                                              vm_id,
                                              network_context)
        fake_profile = {'local_link_information':
                        [{'switch_id': '11:22:33:44:55:66',
                          'port_id': 'Tengig0/1'}]}
        profile = self.driver._get_binding_profile(port_context)
        self.assertEqual(profile, fake_profile)

    def test__get_vnic_type(self):
        """Test _get_binding_profile method."""
        tenant_id = 'ten-1'
        network_id = 'net1-id'
        segmentation_id = 1001
        vm_id = 'vm1'
        network_context = self._get_network_context(tenant_id,
                                                    network_id,
                                                    segmentation_id,
                                                    False)

        port_context = self._get_port_context(tenant_id,
                                              network_id,
                                              vm_id,
                                              network_context)
        vnic_type = self.driver._get_vnic_type(port_context)
        self.assertEqual(vnic_type, 'baremetal')


class FakeNetworkContext(object):
    """To generate network context for testing purposes only."""

    def __init__(self, network, segments=None, original_network=None):
        self._network = network
        self._original_network = original_network
        self._segments = segments

    @property
    def current(self):
        return self._network

    @property
    def original(self):
        return self._original_network

    @property
    def network_segments(self):
        return self._segments


class FakePortContext(object):
    """To generate port context for testing purposes only."""

    def __init__(self, port, original_port, network):
        self._port = port
        self._original_port = original_port
        self._network_context = network

    @property
    def current(self):
        return self._port

    @property
    def original(self):
        return self._original_port

    @property
    def network(self):
        return self._network_context
