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

from neutron.db import model_base
from neutron.db import models_v2

import sqlalchemy as sa
# from sqlalchemy import orm


class HPSwitchLAGPort(model_base.BASEV2, models_v2.HasId):
    """Define HP switch LAG port properties."""
    external_lag_id = sa.Column(sa.String(255))


class HPSwitchPort(model_base.BASEV2, models_v2.HasId):
    """Define HP switch port properties."""
    switch_id = sa.Column(sa.String(48))
    port_name = sa.Column(sa.String(255))
    lag_id = sa.Column(sa.String(36),
                       sa.ForeignKey('hpswitchlagports.id',
                                     ondelete='CASCADE'))


class HPIronicSwitchPortMapping(model_base.BASEV2):
    """Define neutron port and HP switch port mapping."""
    neutron_port_id = sa.Column(sa.String(36))
    switch_port_id = sa.Column(sa.String(36),
                               sa.ForeignKey('hpswitchports.id',
                                             ondelete='CASCADE'),
                               primary_key=True)
    lag_id = sa.Column(sa.String(36),
                       sa.ForeignKey('hpswitchlagports.id',
                                     ondelete='CASCADE'))
    access_type = sa.Column(sa.String(36))
    segmentation_id = sa.Column(sa.Integer)
    host_id = sa.Column(sa.String(36))


class BNPPhysicalSwitchPort(model_base.BASEV2, models_v2.HasId):
    """Define physical switch port properties."""
    __tablename__ = "bnp_physical_switch_ports"
    switch_id = sa.Column(sa.String(255), nullable=False)
    interface_name = sa.Column(sa.String(255), nullable=False)
    ifindex = sa.Column(sa.String(255), nullable=False)
    port_status = sa.Column(sa.String(16), nullable=False)
    sa.PrimaryKeyConstraint('id')
    __table_args__ = (sa.PrimaryKeyConstraint('id'),
                      sa.UniqueConstraint('switch_id',
                                          'interface_name'),)
    sa.ForeignKeyConstraint(['switch_id'],
                            ['bnp_physical_switches.id'],
                            ondelete='CASCADE')


class BNPPhysicalSwitch(model_base.BASEV2, models_v2.HasId):
    """Define physical switch properties."""
    __tablename__ = "bnp_physical_switches"
    ip_address = sa.Column(sa.String(64), nullable=False)
    mac_address = sa.Column(sa.String(32), nullable=True)
    status = sa.Column(sa.String(16), nullable=False)
    access_protocol = sa.Column(sa.String(16), nullable=False)
    vendor = sa.Column(sa.String(16), nullable=False)
    write_community = sa.Column(sa.String(255), nullable=True)
    security_name = sa.Column(sa.String(255), nullable=True)
    auth_protocol = sa.Column(sa.String(16), nullable=True)
    auth_key = sa.Column(sa.String(255), nullable=True)
    priv_protocol = sa.Column(sa.String(16), nullable=True)
    priv_key = sa.Column(sa.String(255), nullable=True)
    security_level = sa.Column(sa.String(16), nullable=True)
    __table_args__ = (sa.PrimaryKeyConstraint('id', 'ip_address'),)


class BNPSwitchPortMapping(model_base.BASEV2):
    """Define neutron port and switch port mapping."""
    __tablename__ = "bnp_switch_port_mappings"
    neutron_port_id = sa.Column(sa.String(36), nullable=False)
    switch_port_id = sa.Column(sa.String(255), nullable=False)
    switch_id = sa.Column(sa.String(255), nullable=False)
    __table_args__ = (sa.PrimaryKeyConstraint('neutron_port_id',
                                              'switch_port_id'),)
    sa.ForeignKeyConstraint(['switch_port_id'],
                            ['bnp_physical_switch_ports.id'],
                            ondelete='CASCADE')


class BNPNeutronPort(model_base.BASEV2):
    """Define neutron port properties."""
    __tablename__ = "bnp_neutron_ports"
    neutron_port_id = sa.Column(sa.String(36), nullable=False)
    lag_id = sa.Column(sa.String(36), nullable=True)
    access_type = sa.Column(sa.String(16), nullable=False)
    segmentation_id = sa.Column(sa.Integer, nullable=False)
    bind_status = sa.Column(sa.Boolean(), nullable=True)
    __table_args__ = (sa.PrimaryKeyConstraint('neutron_port_id'),)
    sa.ForeignKeyConstraint(['neutron_port_id'],
                            ['bnp_switch_port_mappings.neutron_port_id'],
                            ondelete='CASCADE')
