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
