# Copyright 2015 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""bm network provisioning

Revision ID: 3297cd3f2323
Revises: start_bm_nw_provisioning
Create Date: 2015-07-06 00:25:06.980102

"""

# revision identifiers, used by Alembic.
revision = '3297cd3f2323'
down_revision = 'start_bm_nw_provisioning'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('hpswitchlagports',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('external_lag_id', sa.String(length=255),
                              nullable=True),
                    sa.PrimaryKeyConstraint('id'))

    op.create_table('hpswitchports',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('switch_id', sa.String(length=48),
                              nullable=False),
                    sa.Column('port_name', sa.String(length=255),
                              nullable=False),
                    sa.Column('lag_id', sa.String(length=36), nullable=True),
                    sa.ForeignKeyConstraint(['lag_id'],
                                            ['hpswitchlagports.id'],
                                            ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'))

    op.create_table('hpironicswitchportmappings',
                    sa.Column('neutron_port_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('switch_port_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('lag_id', sa.String(length=36), nullable=True),
                    sa.Column('access_type', sa.String(length=36),
                              nullable=True),
                    sa.Column('segmentation_id', sa.Integer, nullable=True),
                    sa.Column('host_id', sa.String(length=36), nullable=True),
                    sa.ForeignKeyConstraint(['lag_id'],
                                            ['hpswitchlagports.id'],
                                            ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['switch_port_id'],
                                            ['hpswitchports.id'],
                                            ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('switch_port_id'))
