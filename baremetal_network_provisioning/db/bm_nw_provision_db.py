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
from sqlalchemy.orm import exc

from baremetal_network_provisioning.db import bm_nw_provision_models as models


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


def get_hp_switch_port_by_switchid_portname(context, record_dict):
    """Get hp_switch_port that matches the supplied switch id and port name."""
    try:
        query = context.session.query(models.HPSwitchPort)
        switch_port = query.filter_by(
            switch_id=record_dict['switch_id'],
            port_name=record_dict['port_name']).one()
    except exc.NoResultFound:
        LOG.debug('no hp switch port found for %s and %s',
                  record_dict['switch_id'],
                  record_dict['port_name'])
        return
    return switch_port


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
            bind_requested=record_dict['bind_requested'])
        session.add(mapping)


def delete_hp_ironic_switch_port_mapping(context, record_dict):
    """Delete ironic switch port mapping that matches neutron_port_id."""
    session = context.session
    with session.begin(subtransactions=True):
        if(record_dict['neutron_port_id']):
            session.query(models.HPIronicSwitchPortMapping).filter_by(
                neutron_port_id=record_dict['neutron_port_id']).delete()


def get_hp_ironic_switch_port_mapping_by_neutron_port_id(context, record_dict):
    """Get ironic_switch_port_mapping that matches the supplied id."""
    try:
        query = context.session.query(models.HPIronicSwitchPortMapping)
        port_mapping = query.filter_by(
            neutron_port_id=record_dict['neutron_port_id']).one()
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


def update_hp_ironic_switch_port_mapping_with_seg_id(context, rec_dict):
    """Update hp_ironic_switch_port_mapping."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPIronicSwitchPortMapping).filter_by(
                id=rec_dict['id']).update(
                    {'access_type': rec_dict['access_type'],
                     'segmentation_id': rec_dict['segmentation_id']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no ironic switch port mapping found for id %s',
                  rec_dict['id'])


def update_hp_ironic_switch_port_mapping_with_bind_req(context, rec_dict):
    """Update hp_ironic_switch_port_mapping."""
    try:
        with context.session.begin(subtransactions=True):
            (context.session.query(models.HPIronicSwitchPortMapping).filter_by(
                id=rec_dict['id']).update(
                    {'bind_requested': rec_dict['bind_requested']},
                    synchronize_session=False))
    except exc.NoResultFound:
        LOG.debug('no ironic switch port mapping found for id %s',
                  rec_dict['id'])
