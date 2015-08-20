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

from neutron import context
from neutron.tests.unit import testlib_api

from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.db import bm_nw_provision_models as models


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
                    'bind_requested': True}
        return rec_dict

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
        result = db.get_hp_switch_port_by_switchid_portname(
            self.ctx,
            {'switch_id': "test_switch1", 'port_name': "Tengig0/1"})
        self.assertEqual('test_switch1', result.switch_id)

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
                       'bind_requested': True})
        result = db.get_hp_ironic_swport_map_by_id(
            self.ctx, {'neutron_port_id': "n1234"})
        self.assertEqual(200, result[0].segmentation_id)

    def test_update_hp_ironic_swport_map_with_bind_req(self):
        """Test update_hp_ironic_swport_map_with_bind_req method."""
        self._add_switch_and_lag_port()
        rec_dict = self._get_ironic_switch_port_map_dict()
        db.add_hp_ironic_switch_port_mapping(self.ctx, rec_dict)
        db.update_hp_ironic_swport_map_with_bind_req(
            self.ctx, {'neutron_port_id': "n1234",
                       'bind_requested': False})
        result = db.get_hp_ironic_swport_map_by_id(
            self.ctx, {'neutron_port_id': "n1234"})
        self.assertEqual(False, result[0].bind_requested)

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
