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
from baremetal_network_provisioning.common import exceptions as hp_exec
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.db import bm_nw_provision_models as models
from baremetal_network_provisioning.ml2 import hp_network_provisioning_driver as driver

import mock
from oslo_config import cfg
import requests

from neutron.tests import base

CONF = cfg.CONF


class TestHPNetworkProvisioningDriver(base.BaseTestCase):

    def setUp(self):
        super(TestHPNetworkProvisioningDriver, self).setUp()
        CONF.set_override('base_url', 'fake_url', 'default')
        self.driver = driver.HPNetworkProvisioningDriver()

    def test_create_port_with_200_ok(self):
        """test_create_port_with_valid_device."""
        port_dict = self._get_port_payload()
        res_200 = FakeResponse(200)
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_200):
            with mock.patch.object(db, 'add_hp_switch_port',
                                   return_value=None):
                with mock.patch.object(db, 'add_hp_ironic_switch_port_mapping',
                                       return_value=None):
                    self.driver.create_port(port_dict)

    def test_create_port_with_connection_failed(self):
        """test_create_port_with_connection_failed."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(503, headers={'retry-after': '10'},
                                   reason="connection error")
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            self.assertRaises(hp_exec.ConnectionFailed,
                              self.driver.create_port,
                              port_dict)

    def test_create_port_with_invalid_device(self):
        """test_create_port_with_invalid_device."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(404, headers={'retry-after': '10'})
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            error = self.assertRaises(hp_exec.ConnectionFailed,
                                      self.driver.create_port,
                                      port_dict)
            self.assertEqual(' Connection has failed: 404 Client Error: None',
                             error.msg)

    def test_bind_port_to_segment_success(self):
        """test_bind_port_to_segment_success."""
        port_dict = self._get_port_payload()
        res_204 = FakeResponse(204)
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_204):
            with mock.patch.object(db,
                                   'update_hp_ironic_swport_map_with_seg_id',
                                   return_value=None):
                    value = self.driver.bind_port_to_segment(port_dict)
                    self.assertEqual(value, hp_const.BIND_SUCCESS)

    def test_bind_port_to_segment_with_connection_failed(self):
        """test_bind_port_to_segment_with_connection_failed."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(503, headers={'retry-after': '10'},
                                   reason="connection_error")
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            self.assertRaises(hp_exec.ConnectionFailed,
                              self.driver.bind_port_to_segment,
                              port_dict)

    def test_bind_port_to_segment_with_failure(self):
        """test_bind_port_to_segment_with_failure."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(203, headers={'retry-after': '10'})
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            value = self.driver.bind_port_to_segment(port_dict)
            self.assertEqual(value, hp_const.BIND_FAILURE)

    def test_update_port(self):
        """test_update_port."""
        pass

    def test_delete_port(self):
        """test_delete_port."""
        with mock.patch.object(db,
                               'get_hp_ironic_swport_map_by_id',
                               return_value=models.HPIronicSwitchPortMapping):
            with mock.patch.object(db,
                                   'delete_hp_switch_port',
                                   return_value=None):
                self.driver.delete_port('fake_id')

    def _get_port_payload(self):
        """_get_port_payload for processing requests."""
        port_dict = {'port':
                     {'segmentation_id': '1001',
                      'bind_requested': True,
                      'access_type': hp_const.ACCESS,
                      'switchports':
                      [{'port_id': 'Ten-GigabitEthernet1/0/35',
                          'switch_id': '44:31:92:61:89:d2'}],
                      'id': '321f506f-5f0d-435c-9c23-c2a11f78c3e3',
                      'is_lag': False}}
        return port_dict


class FakeResponse(requests.Response):
    def __init__(self, status_code=None, text=None, headers=None, reason=None):
        self._text = text
        self.status_code = status_code
        self.reason = reason
        if headers is not None:
            self.headers = headers

    @property
    def text(self):
        return self._text
