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

from ironic.common import exception
from oslo_log import log as logging
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp import error as snmp_error

LOG = logging.getLogger(__name__)


Auth_protocol = {None: cmdgen.usmNoAuthProtocol,
                 'md5': cmdgen.usmHMACMD5AuthProtocol,
                 'sha': cmdgen.usmHMACSHAAuthProtocol}

Priv_protocol = {None: cmdgen.usmNoPrivProtocol,
                 'des': cmdgen.usmDESPrivProtocol,
                 'des56': cmdgen.usmDESPrivProtocol,
                 '3des': cmdgen.usm3DESEDEPrivProtocol,
                 'aes': cmdgen.usmAesCfb128Protocol,
                 'aes128': cmdgen.usmAesCfb128Protocol,
                 'aes192': cmdgen.usmAesCfb192Protocol,
                 'aes256': cmdgen.usmAesCfb256Protocol}


class SNMPClient(object):

    """SNMP client object.

    """
    def __init__(self, ip_address, access_protocol,
                 write_community=None, security_name=None,
                 auth_protocol=None, auth_key=None,
                 priv_protocol=None, priv_key=None):
        self.ip_address = ip_address
        self.access_protocol = access_protocol
        if self.access_protocol == constants.SNMP_V3:
            self.security_name = security_name
            if auth_protocol:
                self.auth_protocol = Auth_protocol[auth_protocol]
                self.auth_key = auth_key
            if priv_protocol:
                self.priv_protocol = Priv_protocol[priv_protocol]
                self.priv_key = priv_key
        else:
            self.write_community = write_community
        self.cmd_gen = cmdgen.CommandGenerator()

    def _get_auth(self):
        """Return the authorization data for an SNMP request.

        """
        if self.access_protocol == constants.SNMP_V3:
            return cmdgen.UsmUserData(self.security_name,
                                      authKey=self.auth_key,
                                      privKey=self.priv_key,
                                      authProtocol=self.auth_protocol,
                                      privProtocol=self.priv_protocol)
        else:
            mp_model = 1 if self.access_protocol == constants.SNMP_V2C else 0
            return cmdgen.CommunityData(self.write_community,
                                        mpModel=mp_model)

    def _get_transport(self):
        """Return the transport target for an SNMP request.

        """
        return cmdgen.UdpTransportTarget(
            (self.ip_address, constants.SNMP_PORT), timeout=1, retries=5)

    def get(self, oid):
        """Use PySNMP to perform an SNMP GET operation on a single object.

        """
        try:
            results = self.cmd_gen.getCmd(self._get_auth(),
                                          self._get_transport(),
                                          oid)
        except snmp_error.PySnmpError as e:
            raise exception.SNMPFailure(operation="GET", error=e)

        error_indication, error_status, error_index, var_binds = results

        if error_indication:
            raise exception.SNMPFailure(operation="GET",
                                        error=error_indication)

        if error_status:
            raise exception.SNMPFailure(operation="GET",
                                        error=error_status.prettyPrint())

        return var_binds

    def get_bulk(self, *oids):
        try:
            results = self.cmd_gen.bulkCmd(self._get_auth(),
                                           self._get_transport(),
                                           0, 52,
                                           *oids
                                           )
        except snmp_error.PySnmpError as e:
            raise exception.SNMPFailure(operation="GET", error=e)

        error_indication, error_status, error_index, var_binds = results

        if error_indication:
            raise exception.SNMPFailure(operation="GET",
                                        error=error_indication)

        if error_status:
            raise exception.SNMPFailure(operation="GET",
                                        error=error_status.prettyPrint())

        return var_binds


def get_client(snmp_info):
    """Create and return an SNMP client object.

    """
    return SNMPClient(snmp_info["ip_address"],
                      snmp_info["access_protocol"],
                      snmp_info.get("write_community"),
                      security_name=snmp_info['security_name'],
                      auth_protocol=snmp_info['auth_protocol'],
                      auth_key=snmp_info['auth_key'],
                      priv_protocol=snmp_info['priv_protocol'],
                      priv_key=snmp_info['priv_key']
                      )
