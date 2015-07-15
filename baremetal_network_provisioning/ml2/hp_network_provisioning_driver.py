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
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils
import requests

from baremetal_network_provisioning.common import exceptions as hp_exec
from baremetal_network_provisioning.ml2 import network_provisioning_api as api


LOG = logging.getLogger(__name__)
hp_opts = [
    cfg.StrOpt('url',
               help=_("Base HTTP URL of  SDN controller")),
    cfg.StrOpt('auth_token',
               default='AuroraSdnToken37',
               help=_("Auth token of SDN controller")),
    cfg.StrOpt('ca_cert',
               default='None',
               help=_("full path to the certificate file containing the"
                      "SDN Controller")),
    cfg.StrOpt('timeout',
               default='30',
               help=_("Timeout in seconds to wait for SDN HTTP request"
                      "completion.")),
]
cfg.CONF.register_opts(hp_opts, "default")


class HPNetworkProvisioningDriver(api.NetworkProvisioningApi):
    """Back-end mechanism driver implementation for bare

    metal provisioning.
    """

    def initialize(self):
        """initialize the network provision driver."""
        self.conf = cfg.CONF
        self._validate_config()
        self.base_url = self.conf.np_hp.get('base_url')
        self.auth_token = self.conf.np_hp.get('auth_token')
        self.ca_cert = self.conf.np_hp.get('ca_cert')
        self.verify_cert = False
        self.timeout = self.conf.np_hp.get('timeout')

    def create_port(self, port_dict):
        LOG.debug("create_port called in HPNetworkProvisioningDriver")
        """create_port. This call makes the REST request to the external
        SDN controller for provision VLAN for the switch port where
        bare metal is connected.
        """
        pass

    def bind_port_to_segment(self, port_dict):
        """bind_port_to_network. This call makes the REST request to the external

        SDN controller for provision VLAN for the switch port where
        bare metal is connected.
        """
        # TODO(Selvakumar) this return is just for testing!
        pass

    def update_port(self, port_dict):
        """update_port. This call makes the REST request to the external

        SDN controller for provision VLAN on switch port where bare metal
        is connected.
        """
        pass

    def delete_port(self, port_id):
        """delete_port. This call makes the REST request to the external

        SDN controller for un-configure  VLAN for the switch port where
        bare metal is connected.
        """
        if not port_id:
            LOG.debug("delete_port port_id is empty")
            return
        # need to discuss how to get the switch_port_id for the remove vlan
        # is empty dict enough for provisioning?

    def _do_request(self, method, urlpath, obj):
        """Send request to the SDN controller."""
        headers = {'Content-Type': 'application/json'}
        headers['X-Auth-Token'] = self.auth_token
        if not self.ca_cert:
            self.verify_cert = False
        else:
            self.verify_cert = self.ca_cert if self.ca_cert else True
        data = jsonutils.dumps(obj, indent=2) if obj else None
        r = requests.request(method, url=urlpath,
                             headers=headers, data=data,
                             verify=self.verify_cert,
                             timeout=self.timeout)
        r.raise_for_status()

    def _frame_port_url(self, switch_id):
        """Frame the physical port URL for SDN controller."""
        switch_port_url = switch_id + '/physicalinterfaces'
        url = self.base_url + '/' + switch_port_url
        return url

    def _validate_config(self):
        if self.conf.np_hp.get('auth_token') == '':
            msg = _('Required option auth_token is not set')
            LOG.error(msg)
            raise hp_exec.HPNetProvisioningConfigError(msg=msg)
        if self.conf.np_hp.get('base_url') == '':
            msg = _('Required option base_url is not set')
            LOG.error(msg)
            raise hp_exec.HPNetProvisioningConfigError(msg=msg)
        if self.conf.np_hp.get('timeout') == '':
            msg = _('Required option timeout is not set')
            LOG.error(msg)
            raise hp_exec.HPNetProvisioningConfigError(msg=msg)
        if self.conf.np_hp.get('ca_cert') == '':
            msg = _('Required option ca_cert is not set')
            LOG.error(msg)
            raise hp_exec.HPNetProvisioningConfigError(msg=msg)
