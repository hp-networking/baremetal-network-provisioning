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


class SNMPDiscoveryDriver(object):

    def __init__(self, snmp_info):
        self.snmp_info = snmp_info
        self.client = snmp_client.get_client(snmp_info)

    def discover_switch(self):
        mac_addr = self.get_mac_addr()
        ports_dict = self.get_ports_info()
        switch = {'mac_address': mac_addr, 'ports': ports_dict}
        return switch

    def get_sys_name(self):
        oid = constants.OID_SYS_NAME
        varBinds = self.client.get(oid)
        for name, val in varBinds:
            return val.prettyPrint()

    def get_mac_addr(self):
        oid = constants.OID_MAC_ADDRESS
        var_binds = self.client.get(oid)
        for name, val in var_binds:
            mac = val.prettyPrint().zfill(12)
            mac = mac[2:]
            mac_addr = ':'.join([mac[i:i + 2] for i in range(0, 12, 2)])
            return mac_addr

    def get_ports_info(self):

        oids = [constants.OID_PORTS,
                constants.OID_IF_INDEX,
                constants.OID_IF_TYPE,
                constants.OID_PORT_STATUS]
        var_binds = self.client.get_bulk(*oids)
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

    def get_port_status(self, ifindex):

        oid = constants.OID_PORT_STATUS + '.' + ifindex
        oid = oid.encode("utf-8")
        var_bind = self.client.get(oid)
        for name, val in var_bind:
            ret = val
        return ret
