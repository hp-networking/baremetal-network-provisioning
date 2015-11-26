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

from oslo_config import cfg
from oslo_log import log as logging
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp import error as snmp_error

LOG = logging.getLogger(__name__)

hp_opts = [
    cfg.IntOpt('snmp_retries',
               default=3,
               help=_("Number of retries to be done")),
    cfg.IntOpt('snmp_timeout',
               default=3,
               help=_("Timeout in seconds to wait for SNMP request"
                      "completion.")),
]
cfg.CONF.register_opts(hp_opts, "default")


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
        self.conf = cfg.CONF
        self.ip_address = ip_address
        self.access_protocol = access_protocol
        self.timeout = self.conf.default.get('snmp_timeout')
        self.retries = self.conf.default.get('snmp_retries')
        if self.access_protocol == constants.SNMP_V3:
            self.security_name = security_name
            self.auth_protocol = Auth_protocol[auth_protocol]
            self.auth_key = auth_key
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
            (self.ip_address, constants.SNMP_PORT),
            timeout=self.timeout,
            retries=self.retries)

    def get(self, oid):
        """Use PySNMP to perform an SNMP GET operation on a single object.

        """
        try:
            results = self.cmd_gen.getCmd(self._get_auth(),
                                          self._get_transport(),
                                          oid)
        except snmp_error.PySnmpError as e:
            raise exceptions.SNMPFailure(operation="GET", error=e)

        error_indication, error_status, error_index, var_binds = results

        if error_indication:
            raise exceptions.SNMPFailure(operation="GET",
                                         error=error_indication)

        if error_status:
            raise exceptions.SNMPFailure(operation="GET",
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
            raise exceptions.SNMPFailure(operation="GET_BULK", error=e)

        error_indication, error_status, error_index, var_binds = results

        if error_indication:
            raise exceptions.SNMPFailure(operation="GET_BULK",
                                         error=error_indication)

        if error_status:
            raise exceptions.SNMPFailure(operation="GET_BULK",
                                         error=error_status.prettyPrint())

        return var_binds


def get_client(snmp_info):
    """Create and return an SNMP client object.

    """
    return SNMPClient(snmp_info['ip_address'],
                      snmp_info['access_protocol'],
                      snmp_info['write_community'],
                      snmp_info['security_name'],
                      snmp_info['auth_protocol'],
                      snmp_info['auth_key'],
                      snmp_info['priv_protocol'],
                      snmp_info['priv_key']
                      )
