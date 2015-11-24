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
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.ml2 import network_provisioning_api as api

import webob.exc as wexc

from neutron.api.v2 import base
from neutron import context as neutron_context
from neutron.i18n import _LE
from neutron.i18n import _LI
from neutron.plugins.ml2.common import exceptions as ml2_exc

from oslo_log import log as logging
from oslo_utils import importutils

from baremetal_network_provisioning.common import constants
LOG = logging.getLogger(__name__)


class HPSNMPProvisioningDriver(api.NetworkProvisioningApi):
    """Back-end mechanism driver implementation for bare

    metal provisioning.
    """

    def __init__(self):
        """initialize the snmp driver."""
        # TODO(selva) need to check how we can load dynamically
        drvr = 'baremetal_network_provisioning.drivers.snmp_driver.SNMPDriver'
        self.context = neutron_context.get_admin_context()
        self._load_drivers(drvr)

    def create_port(self, port):
        """create_port ."""
        LOG.info(_LI('create_port called from back-end mechanism driver'))
        switchports = port['port']['switchports']
        for switchport in switchports:
            switch_mac_id = switchport['switch_id']
            port_id = switchport['port_id']
            bnp_switch = db.get_bnp_phys_switch_by_mac(self.context,
                                                       switch_mac_id)
            phys_port = db.get_bnp_phys_port(self.context,
                                             bnp_switch.id,
                                             port_id)
            # check for port and switch level existence
            if not bnp_switch:
                LOG.error(_LE("No physical switch found '%s' "), switch_mac_id)
                self._raise_ml2_error(wexc.HTTPNotFound, 'create_port')
            if not phys_port:
                LOG.error(_LE("No physical port found for '%s' "), phys_port)
                self._raise_ml2_error(wexc.HTTPNotFound, 'create_port')

    def bind_port_to_segment(self, port):
        """bind_port_to_segment ."""
        LOG.info(_LI('bind_port_to_segment called from back-end mech driver'))
        switchports = port['port']['switchports']
        for switchport in switchports:
            switch_id = switchport['switch_id']
            bnp_switch = db.get_bnp_phys_switch_by_mac(self.context,
                                                       switch_id)
            port_name = switchport['port_id']
            if not bnp_switch:
                self._raise_ml2_error(wexc.HTTPNotFound, 'create_port')
            phys_port = db.get_bnp_phys_port(self.context,
                                             bnp_switch.id,
                                             port_name)
            if not phys_port:
                self._raise_ml2_error(wexc.HTTPNotFound, 'create_port')
            switchport['ifindex'] = phys_port.ifindex
        credentials_dict = port.get('port')
        cred_dict = self._get_credentials_dict(bnp_switch)
        credentials_dict['credentials'] = cred_dict
        try:
            self.protocol_driver.set_isolation(port)
            port_id = port['port']['id']
            segmentation_id = port['port']['segmentation_id']
            mapping_dict = {'neutron_port_id': port_id,
                            'switch_port_id': phys_port.id,
                            'switch_id': bnp_switch.id,
                            'lag_id': None,
                            'access_type': constants.ACCESS,
                            'segmentation_id': int(segmentation_id),
                            'bind_status': 0
                            }
            db.add_bnp_switch_port_map(self.context, mapping_dict)
            db.add_bnp_neutron_port(self.context, mapping_dict)
            return constants.BIND_SUCCESS
        except Exception as e:
            LOG.error(_LE("Exception in configuring VLAN '%s' "), e)
            return constants.BIND_FAILURE

    def update_port(self, port):
        """update_port ."""
        # TODO(selva) yet to implement!
        pass

    def delete_port(self, port_id):
        """delete_port ."""
        port_map = db.get_bnp_neutron_port(self.context, port_id)
        is_last_port_in_vlan = False
        if not port_map:
            self._raise_ml2_error(wexc.HTTPNotFound, 'delete_port')
        seg_id = port_map.segmentation_id
        bnp_sw_map = db.get_bnp_switch_port_mappings(self.context, port_id)
        switch_port_id = bnp_sw_map[0].switch_port_id
        bnp_switch = db.get_bnp_phys_switch(self.context,
                                            bnp_sw_map[0].switch_id)
        cred_dict = self._get_credentials_dict(bnp_switch)
        phys_port = db.get_bnp_phys_port_by_id(self.context,
                                               switch_port_id)
        result = db.get_bnp_neutron_port_by_seg_id(self.context, seg_id)
        if not result:
            LOG.error(_LE("No neutron port is associated with the phys port"))
            self._raise_ml2_error(wexc.HTTPNotFound, 'delete_port')
        if len(result) == 1:
            # to prevent snmp set from the same VLAN
            is_last_port_in_vlan = True
        port_dict = {'port':
                     {'id': port_id,
                      'segmentation_id': seg_id,
                      'ifindex': phys_port.ifindex,
                      'is_last_port_vlan': is_last_port_in_vlan
                      }
                     }
        credentials_dict = port_dict.get('port')
        credentials_dict['credentials'] = cred_dict
        try:
            self.protocol_driver.delete_isolation(port_dict)
            db.delete_bnp_neutron_port(self.context, port_id)
            db.delete_bnp_switch_port_mappings(self.context, port_id)
        except Exception as e:
            LOG.error(_LE("Error in deleting the port '%s' "), e)
            self._raise_ml2_error(wexc.HTTPNotFound, 'delete_port')

    def _load_drivers(self, driver_str):
        """Loads Facet drivers."""
        if not driver_str:
            raise SystemExit(_('A facet driver'
                               'must be specified'))
        self.protocol_driver = importutils.import_object(driver_str)

    def _raise_ml2_error(self, err_type, method_name):
        base.FAULT_MAP.update({ml2_exc.MechanismDriverError: err_type})
        raise ml2_exc.MechanismDriverError(method=method_name)

    def _get_credentials_dict(self, bnp_switch):
        if not bnp_switch:
            self._raise_ml2_error(wexc.HTTPNotFound, 'create_port')
        creds_dict = {}
        creds_dict['ip_address'] = bnp_switch.ip_address
        creds_dict['write_community'] = bnp_switch.write_community
        creds_dict['security_name'] = bnp_switch.security_name
        creds_dict['security_level'] = bnp_switch.security_level
        creds_dict['auth_protocol'] = bnp_switch.auth_protocol
        creds_dict['access_protocol'] = bnp_switch.access_protocol
        creds_dict['auth_key'] = bnp_switch.auth_key
        creds_dict['priv_protocol'] = bnp_switch.priv_protocol
        creds_dict['priv_key'] = bnp_switch.priv_key
        return creds_dict
