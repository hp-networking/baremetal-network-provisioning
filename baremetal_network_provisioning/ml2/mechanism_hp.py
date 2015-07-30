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
from oslo_utils import importutils

from neutron.common import constants as n_const
from neutron.extensions import portbindings
from neutron.i18n import _LE
from neutron.plugins.common import constants
from neutron.plugins.ml2.common import exceptions as ml2_exc
from neutron.plugins.ml2 import driver_api as api

from baremetal_network_provisioning.common import constants as hp_const
from baremetal_network_provisioning.common import exceptions as hp_exc


LOG = logging.getLogger(__name__)
hp_opts = [
    cfg.StrOpt('net_provisioning_driver',
               default='baremetal_network_provisioning.ml2'
               '.hp_network_provisioning_driver.HPNetworkProvisioningDriver',
               help=_("Driver to provision networks on the switches in"
                      "the cloud fabric")),
]
cfg.CONF.register_opts(hp_opts, "ml2_hp")


class HPMechanismDriver(api.MechanismDriver):
    """Ml2 Mechanism front-end driver interface for bare

    metal provisioning.
    """

    def initialize(self):
        self.conf = cfg.CONF
        self._load_drivers()
        self.vif_type = hp_const.HP_VIF_TYPE
        self.vif_details = {portbindings.CAP_PORT_FILTER: True}

    def _load_drivers(self):
        """Loads back end network provision driver from configuration."""
        driver_obj = self.conf.ml2_hp.net_provisioning_driver
        if not driver_obj:
            raise SystemExit(_('A network provisioning driver'
                               'must be specified'))
        self.np_driver = importutils.import_object(driver_obj)

    def create_port_precommit(self, context):
        """create_port_precommit."""
        if not self._is_port_of_interest(context):
            return
        port_dict = self._construct_port(context)
        LOG.debug("create_port_precommit  port dict %s(port_dict)",
                  {'port_dict': port_dict})
        try:
            self.np_driver.create_port(port_dict)
        except hp_exc.HPNetProvisioningDriverError as e:
            LOG.error(_LE("HPNetProvisioningDriverError"), e)
            raise ml2_exc.MechanismDriverError()

    def create_port_postcommit(self, context):
        """create_port_postcommit."""
        pass

    def update_port_precommit(self, context):
        """update_port_precommit."""
        vnic_type = self._get_vnic_type(context)
        binding_profile = self._get_binding_profile(context)
        if vnic_type != portbindings.VNIC_BAREMETAL or not binding_profile:
            return
        profile = self._get_binding_profile(context)
        port_dict = self._construct_port(context)
        bind_requested = profile.get('bind_requested')
        bind_port_dict = port_dict.get('port')
        bind_port_dict['bind_requested'] = bind_requested
        try:
            self.np_driver.update_port(port_dict)
        except hp_exc.HPNetProvisioningDriverError as e:
            LOG.error(_LE("HPNetProvisioningDriverError"), e)
            raise ml2_exc.MechanismDriverError()

    def update_port_postcommit(self, context):
        """update_port_postcommit."""
        pass

    def delete_port_precommit(self, context):
        """delete_port_postcommit."""
        vnic_type = self._get_vnic_type(context)
        port_dict = self._construct_port(context, False)
        if vnic_type == portbindings.VNIC_BAREMETAL:
            try:
                self.np_driver.delete_port(port_dict)
            except hp_exc.HPNetProvisioningDriverError as e:
                LOG.error(_LE("HPNetProvisioningDriverError"), e)
                raise ml2_exc.MechanismDriverError()
            LOG.debug("successfully deleted the baremetal port %(port)s",
                      {'port': context.current['id']})

    def delete_port_postcommit(self, context):
        pass

    def bind_port(self, context):
        """bind_port for claiming the ironic port."""
        LOG.debug("HPMechanismDriver Attempting to bind port %(port)s on "
                  "network %(network)s",
                  {'port': context.current['id'],
                   'network': context.network.current['id']})
        port_id = context.current['id']
        for segment in context.segments_to_bind:
            segmentation_id = segment.get(api.SEGMENTATION_ID)
            if self._is_vlan_segment(segment, context):
                profile = self._get_binding_profile(context)
                port_status = n_const.PORT_STATUS_ACTIVE
                if not self._is_port_of_interest(context):
                    return
                b_requested = profile.get('bind_requested')
                if b_requested is True:
                    port = self._construct_port(context, segmentation_id)
                    try:
                        b_status = self.np_driver.bind_port_to_segment(port)
                    except hp_exc.HPNetProvisioningDriverError as e:
                        LOG.error(_LE("HPNetProvisioningDriverError"
                                      "in bind_port"),
                                  e)
                        raise ml2_exc.MechanismDriverError()
                    if b_status == hp_const.BIND_SUCCESS:
                        context.set_binding(segment[api.ID],
                                            self.vif_type,
                                            self.vif_details,
                                            status=port_status)
                        LOG.debug("port bound using segment for port %(port)s",
                                  {'port': port_id})
                        return
                    else:
                        LOG.debug("port binding pass for %(segment)s",
                                  {'segment': segment})
                        return
            else:
                LOG.debug("Ignoring %(seg)s  for port %(port)s",
                          {'seg': segmentation_id,
                           'port': port_id})
        return

    def _is_vlan_segment(self, segment, context):
        """Verify a segment is valid for the HP MechanismDriver.

        Verify the requested segment is supported by HP and return True or
        False to indicate this to callers.
        """
        network_type = segment[api.NETWORK_TYPE]
        if network_type in [constants.TYPE_VLAN]:
            return True
        else:
            False

    def _construct_port(self, context, segmentation_id=None):
        port = context.current
        port_id = port['id']
        is_lag = False
        bind_port_dict = None
        profile = self._get_binding_profile(context)
        local_link_information = profile.get('local_link_information')
        LOG.debug("_construct_port local link info %(local_info)s",
                  {'local_info': local_link_information})
        if local_link_information and len(local_link_information) > 1:
            is_lag = True
        port_dict = {'port':
                     {'id': port_id,
                      'is_lag': is_lag,
                      'switchports': local_link_information
                      }
                     }
        if segmentation_id:
            bind_port_dict = port_dict.get('port')
            bind_port_dict['segmentation_id'] = segmentation_id
            bind_port_dict['access_type'] = hp_const.ACCESS
        else:
            return port_dict
        final_dict = {'port': bind_port_dict}
        LOG.debug("final port dict  %(final_dict)s",
                  {'final_dict': final_dict})
        return final_dict

    def _get_binding_profile(self, context):
        """get binding profile from port context."""
        profile = context.current.get(portbindings.PROFILE, {})
        if not profile:
            LOG.debug("Missing profile in port binding")
        return profile

    def _get_vnic_type(self, context):
        """get vnic type for baremetal."""
        vnic_type = context.current.get(portbindings.VNIC_TYPE, "")
        if not vnic_type:
            return None
        else:
            return vnic_type

    def _is_port_of_interest(self, context):
        vnic_type = self._get_vnic_type(context)
        binding_profile = self._get_binding_profile(context)
        if vnic_type != portbindings.VNIC_BAREMETAL or not binding_profile:
            return False
        local_link_information = binding_profile.get('local_link_information')
        if not local_link_information:
            LOG.debug("local_link_information list does not exist in profile")
            return False
        return True
