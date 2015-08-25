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
from oslo_utils import uuidutils
import requests

from neutron import context as neutron_context

from baremetal_network_provisioning.common import constants as hp_const
from baremetal_network_provisioning.common import exceptions as hp_exec
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.ml2 import network_provisioning_api as api


LOG = logging.getLogger(__name__)
hp_opts = [
    cfg.StrOpt('base_url',
               help=_("Base HTTP URL of  SDN controller")),
    cfg.StrOpt('auth_token',
               default='AuroraSdnToken37',
               help=_("Authentication token for SDN controller")),
    cfg.StrOpt('ca_cert',
               default=None,
               help=_("full path to the certificate file containing the"
                      "SDN Controller")),
    cfg.StrOpt('timeout',
               default=15,
               help=_("Timeout in seconds to wait for SDN HTTP request"
                      "completion.")),
]
cfg.CONF.register_opts(hp_opts, "default")


class HPNetworkProvisioningDriver(api.NetworkProvisioningApi):
    """Back-end mechanism driver implementation for bare

    metal provisioning.
    """

    def __init__(self):
        """initialize the network provision driver."""
        self.context = neutron_context.get_admin_context()
        self.conf = cfg.CONF
        self.base_url = self.conf.default.base_url
        self.auth_token = self.conf.default.auth_token
        self.ca_cert = self.conf.default.ca_cert
        self.verify_cert = False
        self.timeout = float(self.conf.default.get('timeout'))

    def create_port(self, port_dict):
        """create_port. This call makes the REST request to the external

        SDN controller for provision VLAN for the switch port where
        bare metal is connected.
        """
        LOG.debug("create_port port_dict %(port_dict)s",
                  {'port_dict': port_dict})
        lag_id = None
        switchports = port_dict['port']['switchports']
        neutron_port_id = port_dict['port']['id']
        for switchport in switchports:
            switch_port_id = uuidutils.generate_uuid()
            switch_mac_id = switchport['switch_id']
            rec_dict = {'id': switch_port_id,
                        'switch_id': switch_mac_id,
                        'port_name': switchport['port_id'],
                        'lag_id': None}
            switch_url = self._frame_switch_url(switch_mac_id)
            try:
                resp = self._do_request('GET', switch_url, None)
                LOG.debug("response from SDN controller %(resp)s ",
                          {'resp': resp})
                resp.raise_for_status()
                mapping_dict = {'neutron_port_id': neutron_port_id,
                                'switch_port_id': switch_port_id,
                                'lag_id': lag_id,
                                'access_type': None,
                                'segmentation_id': None,
                                'host_id': None}
                session = self.context.session
                if resp.status_code == requests.codes.OK:
                    with session.begin(subtransactions=True):
                        db.add_hp_switch_port(self.context, rec_dict)
                        db.add_hp_ironic_switch_port_mapping(self.context,
                                                             mapping_dict)
                else:
                    LOG.error(" Given physical switch does not exists")
                    raise hp_exec.HPNetProvisioningDriverError(msg="Failed to"
                                                               "communicate"
                                                               "SDN"
                                                               "Controller")
            except requests.exceptions.Timeout as e:
                LOG.error(" Request timed out in SDN controller : %s", e)
                self._roll_back_created_ports(neutron_port_id)
                raise hp_exec.HPNetProvisioningDriverError(msg="Timed Out"
                                                               "with SDN"
                                                               "controller: %s"
                                                               % e)
            except requests.exceptions.SSLError as e:
                LOG.error(" SSLError to SDN controller : %s", e)
                self._roll_back_created_ports(neutron_port_id)
                raise hp_exec.SslCertificateValidationError(msg=e)
            except Exception as e:
                LOG.error(" ConnectionFailed to SDN controller : %s", e)
                self._roll_back_created_ports(neutron_port_id)
                raise hp_exec.ConnectionFailed(msg=e)

    def bind_port_to_segment(self, port_dict):
        """bind_port_to_network. This call makes the REST request to the

        external SDN controller for provisioning VLAN for the switch port where
        bare metal is connected.
        """
        LOG.debug("bind_port_to_segment with port dict %(port_dict)s",
                  {'port_dict': port_dict})
        bind_dict = self._get_bind_dict(port_dict)
        is_lag = port_dict['port']['is_lag']
        if is_lag:
            resp = self._do_lag_request(port_dict, True, None)
        else:
            resp = self._do_vlan_provisioning(port_dict, True)
        port_id = port_dict['port']['id']
        if resp.status_code == 204:
            db.update_hp_ironic_swport_map_with_seg_id(self.context,
                                                       bind_dict)
            return hp_const.BIND_SUCCESS
        elif resp.status_code == 200:
            LOG.debug("lag request for physicalInterfaces is succeeded")
            lag_id = uuidutils.generate_uuid()
            ext_lag_id = resp.json()['lagId']
            lag_dict = {'id': lag_id,
                        'external_lag_id': ext_lag_id,
                        'neutron_port_id': port_id}
            db.add_hp_switch_lag_port(self.context,
                                      lag_dict)
            db.update_hp_ironic_swport_map_with_seg_id(self.context,
                                                       bind_dict)
            db.update_hp_ironic_swport_map_with_lag_id(self.context,
                                                       lag_dict)
            self._update_hp_sw_lag_id(self.context, lag_dict)
            return hp_const.BIND_SUCCESS
        else:
            return hp_const.BIND_FAILURE

    def update_port(self, port_dict):
        """update_port. This call makes the REST request to the external

        SDN controller for provision VLAN on switch port where bare metal
        is connected.
        """
        pass

    def delete_port(self, port_id):
        """delete_port. This call makes the REST request to the external

        SDN controller for un provision VLAN for the switch port where
        bare metal is connected.
        """
        LOG.debug("delete_port with port_id %(port_id)s",
                  {'port_id': port_id})
        rec_dict = {'neutron_port_id': port_id}
        ir_ports = db.get_hp_ironic_swport_map_by_id(self.context,
                                                     rec_dict)
        if len(ir_ports) > 1:
            is_lag = True
        else:
            is_lag = False
        if is_lag:
            ext_lag_id = self._get_ext_lag_id_by_port_id(port_id)
            resp = self._do_lag_request(None, False, ext_lag_id)
            if resp and resp.status_code == 204:
                for ironic_port in ir_ports:
                    hp_sw_port_id = ironic_port.switch_port_id
                    hp_sw_port_dict = {'id': hp_sw_port_id}
                    lag_id = ironic_port.lag_id
                    db.delete_hp_switch_port(self.context, hp_sw_port_dict)
                if lag_id:
                    lag_dict = {'id': lag_id}
                    db.delete_hp_switch_lag_port(self.context, lag_dict)
            else:
                LOG.error("Could not delete the switch port due to invalid"
                          "response")
        else:
            ir_prt_map = db.get_hp_ironic_swport_map_by_id(self.context,
                                                           rec_dict)
            hp_switch_port_id = ir_prt_map[0].switch_port_id
            hp_sw_port_dict = {'id': hp_switch_port_id}
            switch_port_map = db.get_hp_switch_port_by_id(self.context,
                                                          hp_sw_port_dict)
            switch_id = switch_port_map.switch_id
            port_name = switch_port_map.port_name
            inner_switchports_dict = {'port_id': port_name, 'switch_id':
                                      switch_id}
            switchports_list = []
            switchports_list.append(inner_switchports_dict)
            switchports_dict = {'switchports': switchports_list}
            switchports_dict['segmentation_id'] = ir_prt_map[0].segmentation_id
            switchports_dict['access_type'] = hp_const.ACCESS
            LOG.debug(" switchports_dict %(switchports_dict)s ",
                      {'switchports_dict': switchports_dict})
            delete_port_dict = {'port': switchports_dict}
            resp = self._do_vlan_provisioning(delete_port_dict, False)
            if resp and resp.status_code == 204:
                db.delete_hp_switch_port(self.context, hp_sw_port_dict)
            else:
                LOG.error("Could not delete the switch port due to invalid"
                          "response")

    def _do_request(self, method, urlpath, obj):
        """Send REST request to the SDN controller."""
        headers = {'Content-Type': 'application/json'}
        headers['X-Auth-Token'] = self.auth_token
        if not self.ca_cert:
            self.verify_cert = False
        else:
            self.verify_cert = self.ca_cert if self.ca_cert else True
        data = jsonutils.dumps(obj, indent=2) if obj else None
        response = requests.request(method, url=urlpath,
                                    headers=headers, data=data,
                                    verify=self.verify_cert,
                                    timeout=self.timeout)
        response.raise_for_status()
        return response

    def _frame_port_url(self, switch_id):
        """Frame the physical port URL for SDN controller."""
        switch_port_url = switch_id + '/physicalInterfaces/'
        url = self.base_url + '/' + 'devices' + '/' + switch_port_url
        return url

    def _frame_switch_url(self, switch_id):
        """Frame the physical switch URL for SDN controller."""
        url = self.base_url + '/' + 'devices' + '/' + switch_id
        return url

    def _frame_lag_url(self):
        """Frame the lag URL for SDN controller."""
        url = self.base_url + '/' + 'lagInterfaces'
        return url

    def _frame_lag_url_with_lag_id(self, lag_id):
        """Frame the lag url with id for SDN controller."""
        url = self.base_url + '/' + 'lagInterfaces' + '/' + lag_id
        return url

    def _get_port_pay_load(self, port_dict, include_seg_id=None):
        """Form  port payload for SDN controller REST request."""
        switchports = port_dict['port']['switchports']
        port_list = []
        segmentation_id = port_dict['port']['segmentation_id']
        seg_id_list = []
        seg_id_list.append(str(segmentation_id))
        access_type = port_dict['port']['access_type']
        for switch_port in switchports:
            port_id = switch_port['port_id']
            if include_seg_id:
                res_port_dict = {'port': port_id,
                                 'type': access_type,
                                 'includeVlans': seg_id_list}
            else:
                res_port_dict = {'port': port_id,
                                 'type': access_type,
                                 'excludeVlans': seg_id_list}
            port_list.append(res_port_dict)
        return {'ports': port_list}

    def _get_bind_dict(self, port_dict):
        segmentation_id = port_dict['port']['segmentation_id']
        host_id = port_dict['port']['host_id']
        bind_dict = {'neutron_port_id': port_dict['port']['id'],
                     'access_type': hp_const.ACCESS,
                     'segmentation_id': segmentation_id,
                     'host_id': host_id,
                     }
        return bind_dict

    def _do_vlan_provisioning(self, port_dict, include_seg_id):
        """Provisioning or de-provisioning the VLANs for physical port."""
        switchport = port_dict['port']['switchports']
        if not switchport:
            return
        switch_mac_id = switchport[0]['switch_id']
        put_url = self._frame_port_url(switch_mac_id)
        LOG.debug("_do_vlan_provisioning put_url %(put_url)",
                  {'put_url': put_url})
        try:
            port_pay_load = self._get_port_pay_load(port_dict, include_seg_id)
            LOG.debug("port_pay_load %(port_pay_load)s ",
                      {'port_pay_load': port_pay_load})
            resp = self._do_request('PUT', put_url, port_pay_load)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout as e:
            LOG.error("Timed out in SDN controller : %s", e)
            raise hp_exec.HPNetProvisioningDriverError(msg="Timed Out"
                                                           "with SDN"
                                                           "controller: %s"
                                                           % e)
        except requests.exceptions.SSLError as e:
            LOG.error("SSLError to SDN controller : %s", e)
            raise hp_exec.SslCertificateValidationError(msg=e)
        except Exception as e:
            LOG.error("ConnectionFailed to SDN controller : %s", e)
            raise hp_exec.ConnectionFailed(msg=e)

    def _do_lag_request(self, port_dict, include_seg_id, ext_lag_id):
        """LAG request for lag ports."""
        lag_url = self._frame_lag_url()
        LOG.debug("_do_lag_request put_url %(put_url)",
                  {'put_url': lag_url})
        try:
            if include_seg_id:
                switchport = port_dict['port']['switchports']
                if not switchport:
                    return
                lag_pay_load = self._lag_payload(port_dict)
                LOG.debug("lag_pay_load %(lag_pay_load)s ",
                          {'lag_pay_load': lag_pay_load})
                resp = self._do_request('POST', lag_url, lag_pay_load)
            else:
                lag_url_id = self._frame_lag_url_with_lag_id(ext_lag_id)
                resp = self._do_request('DELETE', lag_url_id, None)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout as e:
            LOG.error("Timed out in SDN controller : %s", e)
            raise hp_exec.HPNetProvisioningDriverError(msg="Timed Out"
                                                           "with SDN"
                                                           "controller: %s"
                                                           % e)
        except requests.exceptions.SSLError as e:
            LOG.error("SSLError to SDN controller : %s", e)
            raise hp_exec.SslCertificateValidationError(msg=e)
        except Exception as e:
            LOG.error("ConnectionFailed to SDN controller : %s", e)
            raise hp_exec.ConnectionFailed(msg=e)

    def _lag_payload(self, port_dict):
        """Form lag payload for SDN controller lAG REST request."""
        link_local_list = port_dict['port']['switchports']
        segmentation_id = port_dict['port']['segmentation_id']
        seg_id_list = []
        seg_id_list.append(str(segmentation_id))
        access_type = port_dict['port']['access_type']
        device_dict = {}
        for switch_port in link_local_list:
            port_id_list = []
            port_id = switch_port['port_id']
            switch_id = switch_port['switch_id']
            port_id_list.append(port_id)
            if switch_id in device_dict:
                inner_port_id_list = device_dict.get(switch_id)
                inner_port_id_list.append(port_id_list[0])
                device_dict.update({switch_id: inner_port_id_list})
            else:
                device_dict.update({switch_id: port_id_list})
        device_port_list = []
        for key, value in device_dict.iteritems():
            device_port_dict = {}
            device_port_dict['deviceId'] = key
            device_port_dict['ports'] = value
            device_port_list.append(device_port_dict)
        return {"devices": device_port_list,
                "type": access_type,
                "vlans": seg_id_list
                }

    def _update_hp_sw_lag_id(self, context, lag_dict):
        """Update hp switch lag_id ."""
        switch_ports = db.get_hp_ironic_swport_map_by_id(context, lag_dict)
        for switch_port in switch_ports:
            sw_port_id = switch_port.switch_port_id
            rec_dict = {'id': sw_port_id, 'lag_id': lag_dict['id']}
            db.update_hp_switch_ports_with_lag_id(context, rec_dict)

    def _get_ext_lag_id_by_port_id(self, port_id):
        """Get external lag_id by neutron port id."""
        neutron_port_dict = {'neutron_port_id': port_id}
        lag_models = db.get_lag_id_by_neutron_port_id(self.context,
                                                      neutron_port_dict)
        for lag_model in lag_models:
            ext_lag = db.get_ext_lag_id_by_lag_id(self.context,
                                                  {'id': lag_model.lag_id})
            ext_lag_id = ext_lag.external_lag_id
            if ext_lag_id:
                break
        return ext_lag_id

    def _roll_back_created_ports(self, neutron_port_id):
        rec_dict = {"neutron_port_id": neutron_port_id}
        hp_sw_ports = db.get_hp_ironic_swport_map_by_id(self.context, rec_dict)
        if not hp_sw_ports:
            return
        for hp_sw_port in hp_sw_ports:
            hp_sw_port_id = hp_sw_port.switch_port_id
            hp_sw_port_dict = {'id': hp_sw_port_id}
            db.delete_hp_switch_port(self.context, hp_sw_port_dict)
        LOG.debug("Roll back for the created ports succeeded")
