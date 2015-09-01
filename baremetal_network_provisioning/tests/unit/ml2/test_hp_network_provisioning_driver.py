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
from baremetal_network_provisioning.common import exceptions as hp_ex
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.db import bm_nw_provision_models as models
from baremetal_network_provisioning.ml2 import (hp_network_provisioning_driver
                                                as driver)

import contextlib

import mock
from oslo_config import cfg
from oslo_serialization import jsonutils
import requests

from neutron.tests import base
CONF = cfg.CONF


class TestHPNetworkProvisioningDriver(base.BaseTestCase):

    def setUp(self):
        super(TestHPNetworkProvisioningDriver, self).setUp()
        CONF.set_override('base_url', 'fake_url', 'default')
        self.driver = driver.HPNetworkProvisioningDriver()
        self._body = {'ports': ['Ten-GigabitEthernet1/0/35']}
        self._lag_body = {'ports': ['Ten-GigabitEthernet1/0/35',
                                    'Ten-GigabitEthernet1/0/36']}

    def test_create_port_with_200_ok(self):
        """Test create port for 200 OK for get devices REST."""
        port_dict = self._get_port_payload()
        self.resp_headers = {"content-type": "application/json"}
        return_value = FakeResponse(status_code=200,
                                    content=jsonutils.dumps(self._body),
                                    headers=self.resp_headers)
        requests.request.return_value = return_value
        with contextlib.nested(mock.patch.object(self.driver,
                                                 '_do_request',
                                                 return_value=return_value),
                               mock.patch.object(db, 'add_hp_switch_port',
                                                 return_value=None),
                               mock.patch.object(db,
                               'add_hp_ironic_switch_port_mapping',
                                                 return_value=None)):
                    self.driver.create_port(port_dict)

    def test_create_lag_port_with_200_ok(self):
        """Test create lag  port for 200 OK for get devices REST."""
        port_dict = self._get_lag_port_payload()
        self.resp_headers = {"content-type": "application/json"}
        return_value = FakeResponse(status_code=200,
                                    content=jsonutils.dumps(self._lag_body),
                                    headers=self.resp_headers)
        requests.request.return_value = return_value
        with contextlib.nested(mock.patch.object(self.driver,
                                                 '_do_request',
                                                 return_value=return_value),
                               mock.patch.object(db, 'add_hp_switch_port',
                                                 return_value=None),
                               mock.patch.object(db,
                               'add_hp_ironic_switch_port_mapping',
                                                 return_value=None)):
                    self.driver.create_port(port_dict)

    def test_create_port_with_connection_failed(self):
        """Test create port with SDN controller error."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(status_code=200,
                                   headers={'retry-after': '10'},
                                   content=self._body)
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            self.assertRaises(hp_ex.ConnectionFailed,
                              self.driver.create_port,
                              port_dict)

    def test_create_port_with_invalid_device(self):
        """Test create port with invalid device."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(content=None, status_code=503,
                                   headers={'retry-after': '10'})
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            error = self.assertRaises(hp_ex.ConnectionFailed,
                                      self.driver.create_port,
                                      port_dict)
            self.assertEqual(' Connection has failed: response is none',
                             error.msg)

    def test_bind_port_to_segment_success(self):
        """Test bind port to segment for success case."""
        port_dict = self._get_port_payload()
        res_204 = FakeResponse(204)
        with contextlib.nested(
            mock.patch.object(self.driver,
                              '_do_request',
                              return_value=res_204),
            mock.patch.object(db,
                              'update_hp_ironic_swport_map_with_seg_id',
                              return_value=None)):
                    value = self.driver.bind_port_to_segment(port_dict)
                    self.assertEqual(value, hp_const.BIND_SUCCESS)

    def test_bind__lag_port_to_segment_success(self):
        """Test bind lag port to segment for success case."""
        port_dict = self._get_lag_port_payload()
        res_204 = FakeResponse(204)
        with contextlib.nested(
            mock.patch.object(self.driver,
                              '_do_request',
                              return_value=res_204),
            mock.patch.object(db,
                              'update_hp_ironic_swport_map_with_seg_id',
                              return_value=None)):
                    value = self.driver.bind_port_to_segment(port_dict)
                    self.assertEqual(value, hp_const.BIND_SUCCESS)

    def test_bind_port_to_segment_with_connection_failed(self):
        """Test bind port to segment_with connection failure

        from SDN controller.
        """
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(503, headers={'retry-after': '10'},
                                   reason="connection_error")
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            self.assertRaises(hp_ex.ConnectionFailed,
                              self.driver.bind_port_to_segment,
                              port_dict)

    def test_bind_port_to_segment_with_failure(self):
        """Test bind port to segment with bind failure."""
        port_dict = self._get_port_payload()
        res_unavail = FakeResponse(203, headers={'retry-after': '10'})
        with mock.patch.object(self.driver,
                               '_do_request',
                               return_value=res_unavail):
            value = self.driver.bind_port_to_segment(port_dict)
            self.assertEqual(value, hp_const.BIND_FAILURE)

    def test_delete_port(self):
        """Test delete ironic port."""
        port_dict = self._get_port_payload()
        res_204 = FakeResponse(204)
        ironic_model = [models.HPIronicSwitchPortMapping]
        sw_port_model = models.HPSwitchPort
        with contextlib.nested(mock.patch.object(self.driver,
                                                 '_do_request',
                                                 return_value=res_204),
                               mock.patch.object(db,
                               'get_hp_ironic_swport_map_by_id',
                                                 return_value=ironic_model),
                               mock.patch.object(db,
                               'get_hp_switch_port_by_id',
                                                 return_value=sw_port_model),
                               mock.patch.object(db,
                                                 'delete_hp_switch_port',
                                                 return_value=None)):
                self.driver.delete_port(port_dict)

    def test_delete_lag_port(self):
        """Test delete lag ironic port."""
        port_dict = self._get_lag_port_payload()
        res_204 = FakeResponse(204)
        ironic_model = [models.HPIronicSwitchPortMapping]
        sw_port_model = models.HPSwitchPort
        with contextlib.nested(mock.patch.object(self.driver,
                                                 '_do_request',
                                                 return_value=res_204),
                               mock.patch.object(db,
                               'get_hp_ironic_swport_map_by_id',
                                                 return_value=ironic_model),
                               mock.patch.object(db,
                               'get_hp_switch_port_by_id',
                                                 return_value=sw_port_model),
                               mock.patch.object(db,
                                                 'delete_hp_switch_port',
                                                 return_value=None)):
                self.driver.delete_port(port_dict)

    def _get_lag_port_payload(self):
        """Get lag port payload for processing requests."""
        port_dict = {'port':
                     {'segmentation_id': '1001',
                      'host_id': 'ironic',
                      'access_type': hp_const.ACCESS,
                      'switchports':
                      [{'port_id': 'Ten-GigabitEthernet1/0/35',
                          'switch_id': '44:31:92:61:89:d2'},
                       {'port_id': 'Ten-GigabitEthernet1/0/36',
                          'switch_id': '44:31:92:61:89:d2'}],
                      'id': '321f506f-5f0d-435c-9c23-c2a11f78c3e3',
                      'is_lag': True}}
        return port_dict

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
                      'is_lag': False}}
        return port_dict


class FakeResponse(requests.Response):
    def __init__(self, status_code=None, body=None, headers=None, reason=None,
                 content=None, encoding=None):
        self._content = content
        self.status_code = status_code
        self.encoding = encoding
        self.reason = reason
        if headers is not None:
            self.headers = headers
