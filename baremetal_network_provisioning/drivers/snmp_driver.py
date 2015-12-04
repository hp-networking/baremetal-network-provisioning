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

from baremetal_network_provisioning.common import constants
from baremetal_network_provisioning.common import exceptions
from baremetal_network_provisioning.common import snmp_client
from baremetal_network_provisioning.drivers import (port_provisioning_driver
                                                    as driver)

from neutron.i18n import _LE
from neutron.i18n import _LI

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class SNMPDriver(driver.PortProvisioningDriver):
    """SNMP Facet driver implementation for bare

    metal provisioning.
    """

    def set_isolation(self, port):
        """set_isolation ."""
        LOG.info(_LI("set_isolation with port '%s' "), port)
        try:
            client = snmp_client.get_client(self._get_switch_dict(port))
            seg_id = port['port']['segmentation_id']
            vlan_oid = constants.OID_VLAN_CREATE + '.' + str(seg_id)
            egress_oid = constants.OID_VLAN_EGRESS_PORT + '.' + str(seg_id)
            snmp_response = self._snmp_get(client, vlan_oid)
            if not snmp_response:
                client.set(vlan_oid, client.get_rfc1902_integer(4))
            nibble_byte = self._get_device_nibble_map(client, egress_oid)
            ifindex = self._get_ifindex_for_port(port)
            bit_map = client.get_bit_map_for_add(int(ifindex), nibble_byte)
            bit_list = []
            for line in bit_map:
                bit_list.append(line)
            set_string = client.get_rfc1902_octet_string(''.join(bit_list))
            client.set(egress_oid, set_string)
        except Exception as e:
            LOG.error(_LE("Exception in configuring VLAN '%s' "), e)
            raise exceptions.SNMPFailure(operation="SET", error=e)

    def delete_isolation(self, port):
        """delete_isolation deletes the vlan from the physical ports."""
        try:
            client = snmp_client.get_client(self._get_switch_dict(port))
            seg_id = port['port']['segmentation_id']
            vlan_oid = constants.OID_VLAN_CREATE + '.' + str(seg_id)
            egress_oid = constants.OID_VLAN_EGRESS_PORT + '.' + str(seg_id)
            nibble_byte = self._get_device_nibble_map(client, egress_oid)
            ifindex = port['port']['ifindex']
            bit_map = client.get_bit_map_for_del(int(ifindex), nibble_byte)
            bit_list = []
            for line in bit_map:
                bit_list.append(line)
            set_string = client.get_rfc1902_octet_string(''.join(bit_list))
            client.set(egress_oid, set_string)
            is_last_port_vlan = port['port']['is_last_port_vlan']
            if is_last_port_vlan:
                client.set(vlan_oid, client.get_rfc1902_integer(6))
        except Exception as e:
            LOG.error(_LE("Exception in deleting VLAN '%s' "), e)
            raise exceptions.SNMPFailure(operation="SET", error=e)

    def create_lag(self, port):
        """create_lag  creates the link aggregation for the physical ports."""

        pass

    def delete_lag(self, port):
        """delete_lag  delete the link aggregation for the physical ports."""
        pass

    def _get_switch_dict(self, port):
        creds_dict = port['port']['credentials']
        ip_address = creds_dict['ip_address']
        write_community = creds_dict['write_community']
        security_name = creds_dict['security_name']
        auth_protocol = creds_dict['auth_protocol']
        auth_key = creds_dict['auth_key']
        priv_protocol = creds_dict['priv_protocol']
        priv_key = creds_dict['priv_key']
        access_protocol = creds_dict['access_protocol']
        switch_dict = {
            'ip_address': ip_address,
            'access_protocol': access_protocol,
            'write_community': write_community,
            'security_name': security_name,
            'auth_protocol': auth_protocol,
            'auth_key': auth_key,
            'priv_protocol': priv_protocol,
            'priv_key': priv_key}
        return switch_dict

    def _get_device_nibble_map(self, snmp_client_info, egress_oid):
        try:
            var_binds = snmp_client_info.get(egress_oid)
        except exceptions.SNMPFailure as e:
            LOG.error(_LE("Exception in _get_device_nibble_map '%s' "), e)
            return
        for name, val in var_binds:
            value = snmp_client_info.get_rfc1902_octet_string(val)
            egress_bytes = (vars(value)['_value'])
        return egress_bytes

    def _get_ifindex_for_port(self, port):
        switchport = port['port']['switchports']
        if not switchport:
            return
        # TODO(selva) for LAG we need to change this code
        ifindex = switchport[0]['ifindex']
        return ifindex

    def _snmp_get(self, snmp_client, oid):
        try:
            snmp_response = snmp_client.get(oid)
        except Exception as e:
            LOG.error(_LE("Error in get response '%s' "), e)
            return None
        return snmp_response
