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
from baremetal_network_provisioning.common import snmp_client
from baremetal_network_provisioning.drivers import discovery_driver_api
from oslo_log import log

LOG = log.getLogger(__name__)


class SNMPDiscoveryDriver(discovery_driver_api.DiscoveryDriverAPI):

    def discover_switch(self, snmp_info):
        LOG.debug(" discover_switch called... %s ", snmp_info)
        mac_addr = self.get_mac_addr(snmp_info)
        ports_dict = self.get_ports_info(snmp_info)
        switch = {'mac_address': mac_addr, 'ports': ports_dict}
        return switch

    def get_sys_name(self, snmp_info):
        client = snmp_client.get_client(snmp_info)
        oid = constants.OID_SYS_NAME
        client.get(oid)

    def get_mac_addr(self, snmp_info):
        client = snmp_client.get_client(snmp_info)
        oid = constants.OID_MAC_ADDRESS
        var_binds = client.get(oid)
        for name, val in var_binds:
            mac = val.prettyPrint().zfill(12)
            mac = mac[2:]
            mac_addr = ':'.join([mac[i:i + 2] for i in range(0, 12, 2)])
            return mac_addr

    def get_ports_info(self, snmp_info):
        client = snmp_client.get_client(snmp_info)
        oids = [constants.OID_IF_INDEX,
                constants.OID_PORTS,
                constants.OID_IF_TYPE,
                constants.OID_PORT_STATUS]
        var_binds = client.get_bulk(*oids)
        ports_dict = []
        for var_bind_table_row in var_binds:
            if_index = (var_bind_table_row[0][1]).prettyPrint()
            port_name = (var_bind_table_row[1][1]).prettyPrint()
            if_type = (var_bind_table_row[2][1]).prettyPrint()
            if if_type == constants.PHY_PORT_TYPE:
                ports_dict.append(
                    {'ifindex': if_index,
                     'interface_name': port_name,
                     'port_status': var_bind_table_row[3][1].prettyPrint()})
        return ports_dict

    def get_ports_status(self, snmp_info):
        client = snmp_client.get_client(snmp_info)
        oids = [constants.OID_IF_INDEX,
                constants.OID_PORT_STATUS]
        var_binds = client.get_bulk(*oids)
        ports_dict = []
        for var_bind_table_row in var_binds:
            if_index = (var_bind_table_row[0][1]).prettyPrint()
            ports_dict.append(
                {'ifindex': if_index,
                 'port_status': var_bind_table_row[1][1].prettyPrint()})
        return ports_dict

    def get_driver_name(self):
        return 'hpe' + constants.PROTOCOL_SNMP
