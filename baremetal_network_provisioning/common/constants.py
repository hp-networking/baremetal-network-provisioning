# Copyright 2015 OpenStack Foundation
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
# service type constants:

TRUNK = 'trunk'
ACCESS = 'access'
BIND_IGNORE = 'bind_ignore'
BIND_SUCCESS = 'bind_success'
BIND_FAILURE = 'bind_failure'
HP_VIF_TYPE = 'hp-ironic'

SUPPORTED_PROTOCOLS = ['snmpv1', 'snmpv2c', 'snmpv3']
SUPPORTED_AUTH_PROTOCOLS = [None, 'md5', 'sha', 'sha1']
SUPPORTED_PRIV_PROTOCOLS = [None, 'des', '3des', 'aes',
                            'des56', 'aes128', 'aes192', 'aes256']

SNMP_V1 = 'snmpv1'
SNMP_V2C = 'snmpv2c'
SNMP_V3 = 'snmpv3'
SNMP_PORT = 161
PHY_PORT_TYPE = '6'

OID_MAC_ADDRESS = '1.0.8802.1.1.2.1.3.2.0'
OID_PORTS = '1.3.6.1.2.1.2.2.1.1'
OID_IF_INDEX = '1.3.6.1.2.1.2.2.1.2'
OID_IF_TYPE = '1.3.6.1.2.1.2.2.1.3'
OID_PORT_STATUS = '1.3.6.1.2.1.2.2.1.8'

Port_status = {'1': 'up',
               '2': 'down',
               '3': 'testing',
               '4': 'unknown',
               '5': 'dormant',
               '6': 'notPresent',
               '7': 'lowerLayerDown'}

Switch_status = {'create': 'CREATED',
                 'enable': 'ENABLED',
                 'disable': 'DISABLED'}
