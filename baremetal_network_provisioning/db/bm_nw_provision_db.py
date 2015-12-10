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

from oslo_log import log as logging
from oslo_utils import uuidutils
from sqlalchemy.orm import exc

from baremetal_network_provisioning.db import bm_nw_provision_models as models

from neutron.db import models_v2
from neutron.i18n import _LE


LOG = logging.getLogger(__name__)


def add_hp_switch_port(context, record_dict):
    """Insert a new switch port to hp_switch_ports."""
    session = context.session
    with session.begin(subtransactions=True):
        switch_port = models.HPSwitchPort(
            id=record_dict['id'],
            switch_id=record_dict['switch_id'],
            port_name=record_dict['port_name'],
            lag_id=record_dict['lag_id'])
        session.add(switch_port)


def delete_hp_switch_port(context, record_dict):
    """Delete switch port that matches the supplied id."""
    session = context.session
    with session.begin(subtransactions=True):
        if(record_dict['id']):
            session.query(models.HPSwitchPort).filter_by(
                id=record_dict['id']).delete()


def get_all_hp_sw_port_by_swchid_portname(context, record_dict):
    """Get hp_switch_port that matches the supplied switch id and port name."""
    try:
        query = context.session.query(models.HPSwitchPort)
        switch_port = query.filter_by(
            switch_id=record_dict['switch_id'],
            port_name=record_dict['port_name']).all()
    except exc.NoResultFound:
        LOG.debug('no hp switch port found for %s and %s',
                  record_dict['switch_id'],
                  record_dict['port_name'])
        return
    return switch_port


def get_hp_ironic_swport_map_by_sw_id(context, record_dict):
    """Get ironic_switch_port_mapping that matches the supplied switch id."""
    try:
        query = context.session.query(models.HPIronicSwitchPortMapping)
        port_mapping = query.filter_by(
            switch_port_id=record_dict['id']).one()
    except exc.NoResultFound:
        LOG.debug('no hp ironic switch port mapping found for switch id %s',
                  record_dict['id'])
        return
    return port_mapping


def add_hp_switch_lag_port(context, record_dict):
    """Insert a new lag port to hp_switch_lag_ports."""
    session = context.session
    with session.begin(subtransactions=True):
        lag_port = models.HPSwitchLAGPort(
            id=record_dict['id'],
            external_lag_id=record_dict['external_lag_id'])
        session.add(lag_port)


def delete_hp_switch_lag_port(context, record_dict):
    """Delete lag port that matches the supplied id."""
    session = context.session
    with session.begin(subtransactions=True):
        if(record_dict['id']):
            session.query(models.HPSwitchLAGPort).filter_by(
                id=record_dict['id']).delete()


def get_hp_switch_lag_port_by_id(context, record_dict):
    """Get hp_switch_lag_port that matches the supplied id."""
    try:
        query = context.session.query(models.HPSwitchLAGPort)
        switch_lag_port = query.filter_by(
            id=record_dict['id']).one()
    except exc.NoResultFound:
        LOG.debug('no hp switch lag port found for %s',
                  record_dict['id'])
        return
    return switch_lag_port


def add_hp_ironic_switch_port_mapping(context, record_dict):
    """Insert a new ironic switch port mapping."""
    session = context.session
    with session.begin(subtransactions=True):
        mapping = models.HPIronicSwitchPortMapping(
            neutron_port_id=record_dict['neutron_port_id'],
            switch_port_id=record_dict['switch_port_id'],
            lag_id=record_dict['lag_id'],
            access_type=record_dict['access_type'],
            segmentation_id=record_dict['segmentation_id'],
            host_id=record_dict['host_id'])
        session.add(mapping)


def delete_hp_ironic_switch_port_mapping(context, record_dict):
    """Delete ironic switch port mapping that matches neutron_port_id."""
    session = context.session
    with session.begin(subtransactions=True):
        if(record_dict['neutron_port_id']):
            session.query(models.HPIronicSwitchPortMapping).filter_by(
                neutron_port_id=record_dict['neutron_port_id']).delete()


def get_hp_ironic_swport_map_by_id(context, record_dict):
    """Get ironic_switch_port_mapping that matches the supplied id."""
    try:
        query = context.session.query(models.HPIronicSwitchPortMapping)
        port_mapping = query.filter_by(
            neutron_port_id=record_dict['neutron_port_id']).all()
    except exc.NoResultFound:
        LOG.debug('no hp ironic switch port mapping found for neutron port%s',
                  record_dict['neutron_port_id'])
        return
    return port_mapping


def update_hp_switch_lag_port(context, rec_dict):
    """Update hp_switch_lag_port."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPSwitchLAGPort).filter_by(
                id=rec_dict['id']).update(
                    {'external_lag_id': rec_dict['external_lag_id']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no lag port found for id %s',
                  rec_dict['id'])


def update_hp_ironic_swport_map_with_seg_id(context, rec_dict):
    """Update hp_ironic_switch_port_mapping."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPIronicSwitchPortMapping).filter_by(
                neutron_port_id=rec_dict['neutron_port_id']).update(
                    {'access_type': rec_dict['access_type'],
                     'host_id': rec_dict['host_id'],
                     'segmentation_id': rec_dict['segmentation_id']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no ironic switch port mapping found for id %s',
                  rec_dict['neutron_port_id'])


def update_hp_ironic_swport_map_with_lag_id(context, rec_dict):
    """Update hp_ironic_switch_port_mapping."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPIronicSwitchPortMapping).filter_by(
                neutron_port_id=rec_dict['neutron_port_id']).update(
                    {'lag_id': rec_dict['id']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no ironic switch port mapping found for id %s',
                  rec_dict['neutron_port_id'])


def update_hp_ironic_swport_map_with_host_id(context, rec_dict):
    """Update hp_ironic_switch_port_mapping."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPIronicSwitchPortMapping).filter_by(
                neutron_port_id=rec_dict['neutron_port_id']).update(
                    {'host_id': rec_dict['host_id']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no ironic switch port mapping found for id %s',
                  rec_dict['neutron_port_id'])


def get_hp_switch_port_by_id(context, record_dict):
    """Get hp_switch_port that matches the supplied switch id."""
    try:
        query = context.session.query(models.HPSwitchPort)
        switch_port = query.filter_by(
            id=record_dict['id']).one()
    except exc.NoResultFound:
        LOG.debug('no hp switch port found for %s',
                  record_dict['id'])
        return
    return switch_port


def update_hp_switch_ports_with_lag_id(context, rec_dict):
    """Update hp switch ports with lag_id."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPSwitchPort).filter_by(
                id=rec_dict['id']).update(
                    {'lag_id': rec_dict['lag_id']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no hp port found for lag_id %s',
                  rec_dict['lag_id'])


def get_lag_id_by_neutron_port_id(context, record_dict):
    """Get lag_id that matches the supplied port id."""
    try:
        query = context.session.query(models.HPIronicSwitchPortMapping)
        switch_port = query.filter_by(
            neutron_port_id=record_dict['neutron_port_id']).all()
    except exc.NoResultFound:
        LOG.debug('no hp lag_id  found for %s',
                  record_dict['neutron_port_id'])
        return
    return switch_port


def get_ext_lag_id_by_lag_id(context, record_dict):
    """Get ext_lag_id  that matches the supplied neutron lag id."""
    try:
        query = context.session.query(models.HPSwitchLAGPort)
        switch_port = query.filter_by(
            id=record_dict['id']).one()
    except exc.NoResultFound:
        LOG.debug('no hp lag_id  found for %s',
                  record_dict['id'])
        return
    return switch_port


def get_subnets_by_network(context, network_id):
        subnet_qry = context.session.query(models_v2.Subnet)
        return subnet_qry.filter_by(network_id=network_id).all()


def add_bnp_phys_switch(context, switch):
    """Add physical switch."""
    session = context.session
    with session.begin(subtransactions=True):
        uuid = uuidutils.generate_uuid()
        phy_switch = models.BNPPhysicalSwitch(
            id=uuid,
            ip_address=switch['ip_address'],
            mac_address=switch['mac_address'],
            status=switch['status'],
            access_protocol=switch['access_protocol'],
            vendor=switch['vendor'],
            write_community=switch['write_community'],
            security_name=switch['security_name'],
            auth_protocol=switch['auth_protocol'],
            auth_key=switch['auth_key'],
            priv_protocol=switch['priv_protocol'],
            priv_key=switch['priv_key'],
            security_level=switch['security_level'])
        session.add(phy_switch)
    return phy_switch


def add_bnp_phys_switch_port(context, port):
    """Add physical switch port."""
    session = context.session
    with session.begin(subtransactions=True):
        uuid = uuidutils.generate_uuid()
        switch_port = models.BNPPhysicalSwitchPort(
            id=uuid,
            switch_id=port['switch_id'],
            interface_name=port['interface_name'],
            ifindex=port['ifindex'],
            port_status=port['port_status'])
        session.add(switch_port)


def add_bnp_neutron_port(context, port):
    """Add neutron port."""
    session = context.session
    with session.begin(subtransactions=True):
        neutron_port = models.BNPNeutronPort(
            neutron_port_id=port['neutron_port_id'],
            lag_id=port['lag_id'],
            access_type=port['access_type'],
            segmentation_id=port['segmentation_id'],
            bind_status=port['bind_status'])
        session.add(neutron_port)


def add_bnp_switch_port_map(context, mapping):
    """Add switch port to neutron port mapping."""
    session = context.session
    with session.begin(subtransactions=True):
        port_map = models.BNPSwitchPortMapping(
            neutron_port_id=mapping['neutron_port_id'],
            switch_port_id=mapping['switch_port_id'],
            switch_id=mapping['switch_id'])
        session.add(port_map)


def get_bnp_phys_switch(context, switch_id):
    """Get physical switch that matches id."""
    try:
        query = context.session.query(models.BNPPhysicalSwitch)
        switch = query.filter_by(id=switch_id).one()
    except exc.NoResultFound:
        LOG.error(_LE("no physical switch found with id: %s"), switch_id)
        return
    return switch


def get_bnp_phys_port(context, sw_id, port_name):
    """Get physical port that matches id and interface_name."""
    try:
        query = context.session.query(models.BNPPhysicalSwitchPort)
        port = query.filter_by(switch_id=sw_id, interface_name=port_name).one()
    except exc.NoResultFound:
        LOG.error(_LE("no physical switch found with mac address: %s"), port)
        return
    return port


def get_bnp_phys_switch_by_ip(context, ip_addr):
    """Get physical switch that matches ip address."""
    try:
        query = context.session.query(models.BNPPhysicalSwitch)
        switch = query.filter_by(ip_address=ip_addr).one()
    except exc.NoResultFound:
        LOG.error(_LE("no physical switch found with ip address: %s"), ip_addr)
        return
    return switch


def get_bnp_phys_port_by_id(context, bnp_port_id):
    """Get physical port that matches id."""
    try:
        query = context.session.query(models.BNPPhysicalSwitchPort)
        port = query.filter_by(id=bnp_port_id).one()
    except exc.NoResultFound:
        LOG.error(_LE('no physical port found with id: %s'), bnp_port_id)
        return
    return port


def get_bnp_neutron_port(context, neutron_port_id):
    """Get bnp neutron port that matches neutron_port_id."""
    try:
        query = context.session.query(models.BNPNeutronPort)
        port_map = query.filter_by(neutron_port_id=neutron_port_id).one()
    except exc.NoResultFound:
        LOG.error(_LE('no port map found with id: %s'), port_map)
        return
    return port_map


def get_bnp_neutron_port_by_seg_id(context, segmentation_id):
    """Get bnp neutron port that matches seg_id."""
    try:
        query = context.session.query(models.BNPNeutronPort)
        port_map = query.filter_by(segmentation_id=segmentation_id).all()
    except exc.NoResultFound:
        LOG.error(_LE('no port map found with id: %s'), segmentation_id)
        return
    return port_map


def get_bnp_switch_port_map_by_switchid(context, switchid):
    """Get switch port map by switch_id."""
    try:
        query = context.session.query(models.BNPSwitchPortMapping)
        port_map = query.filter_by(switch_id=switchid).all()
    except exc.NoResultFound:
        LOG.error(_LE("no switch port mapping found for switch: %s"), switchid)
        return
    return port_map


def get_bnp_switch_port_mappings(context, neutron_port_id):
    """Get switch port map by switch_id."""
    try:
        query = context.session.query(models.BNPSwitchPortMapping)
        port_map = query.filter_by(neutron_port_id=neutron_port_id).all()
    except exc.NoResultFound:
        LOG.error(_LE("no switch port mapping found for switch: %s"),
                  neutron_port_id)
        return
    return port_map


def get_bnp_phys_switch_by_mac(context, mac):
    """Get physical switch that matches mac address."""
    try:
        query = context.session.query(models.BNPPhysicalSwitch)
        switch = query.filter_by(mac_address=mac).one()
    except exc.NoResultFound:
        LOG.error(_LE('no physical switch found with mac address: %s'), mac)
        return
    return switch


def delete_bnp_switch_port_mappings(context, neutron_port_id):
    """Delete mappings that matches neutron_port_id."""
    session = context.session
    with session.begin(subtransactions=True):
        if neutron_port_id:
            session.query(models.BNPSwitchPortMapping).filter_by(
                neutron_port_id=neutron_port_id).delete()


def delete_bnp_phys_switch(context, switch_id):
    """Delete physical switch that matches switch_id."""
    try:
        session = context.session
        with session.begin(subtransactions=True):
            if switch_id:
                session.query(models.BNPPhysicalSwitch).filter_by(
                    id=switch_id).delete()
    except exc.NoResultFound:
        LOG.error(_LE("no switch found for switch id: %s"), switch_id)


def delete_bnp_neutron_port(context, nport_id):
    """Delete neutron port that matches_id."""
    session = context.session
    with session.begin(subtransactions=True):
        if nport_id:
            session.query(models.BNPNeutronPort).filter_by(
                neutron_port_id=nport_id).delete()


def get_all_bnp_phys_switches(context):
    """Get all physical switches."""
    try:
        query = context.session.query(models.BNPPhysicalSwitch)
        switches = query.all()
    except exc.NoResultFound:
        LOG.error(_LE("no physical switch found"))
        return
    return switches


def update_bnp_phys_switch_status(context, sw_id, sw_status):
    """Update physical switch status."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.BNPPhysicalSwitch).filter_by(
                id=sw_id).update(
                    {'status': sw_status},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.error(_LE("no physical switch found for id: %s"), sw_id)


def update_bnp_phys_swport_status(context, swid, port_name, port_status):
    """Update physical switch port status by switch id."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.BNPPhysicalSwitchPort).filter_by(
                switch_id=swid, interface_name=port_name).update(
                    {'port_status': port_status},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.error(_LE("no phy switch port found for "
                      "%(switch_id)s %(port_name)s"),
                  {'switch_id': swid, 'port_name': port_name})


def update_bnp_phys_switch_access_params(context, switch_id, params):
    """Update physical switch with access params."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.BNPPhysicalSwitch).filter_by(
                id=switch_id).update(
                    {'access_protocol': params['access_protocol'],
                     'write_community': params['write_community'],
                     'security_name': params['security_name'],
                     'auth_protocol': params['auth_protocol'],
                     'auth_key': params['auth_key'],
                     'priv_protocol': params['priv_protocol'],
                     'priv_key': params['priv_key'],
                     'security_level': params['security_level']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.error(_LE("no physical switch found for id: %s"), switch_id)


def delete_bnp_phys_switch_ports_by_switchid(context, id):
    """Delete the switch ports of a switch."""
    session = context.session
    with session.begin(subtransactions=True):
        session.query(models.BNPPhysicalSwitchPort).filter_by(
            switch_id=id).delete()


def get_bnp_phys_switch_port_by_id(context, id):
    """Get physical switch port by id."""
    try:
        query = context.session.query(models.BNPPhysicalSwitchPort)
        switch_port = query.filter_by(
            id=id).one()
    except exc.NoResultFound:
        LOG.debug('no physical switch port found for %s', id)
        return
    return switch_port
