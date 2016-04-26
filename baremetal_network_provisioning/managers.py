# Copyright (c) 2016 OpenStack Foundation
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
from neutron._i18n import _LE
from neutron._i18n import _LI

from oslo_config import cfg
from oslo_log import log
import stevedore

LOG = log.getLogger(__name__)


class DiscoveryManager(stevedore.named.NamedExtensionManager):
    """Manage discovery drivers for BNP."""

    def __init__(self):
        # Mapping from discovery type name to DriverManager
        self.drivers = {}

        LOG.info(_LI("Configured discovery type driver names: %s"),
                 cfg.CONF.ml2_hpe.disc_driver)
        super(DiscoveryManager, self).__init__('bnp.disc_driver',
                                               cfg.CONF.ml2_hpe.disc_driver,
                                               invoke_on_load=True)
        LOG.info(_LI("Loaded discovery driver names: %s"), self.names())
        self._register_discovery()

    def _register_discovery(self):
        for ext in self:
            discovery_name = ext.obj.get_driver_name()
            if discovery_name in self.drivers:
                LOG.error(_LE("discovery driver '%(new_driver)s' ignored "
                              " discovery driver '%(old_driver)s' is already"
                              " registered for discovery '%(type)s'"),
                          {'new_driver': ext.name,
                           'old_driver': self.drivers[discovery_name].name,
                           'type': discovery_name})
            else:
                self.drivers[discovery_name] = ext
        LOG.info(_LI("Registered discovery driver: %s"), self.drivers.keys())

    def discovery_driver(self, discovery_type):
        """discovery driver instance."""
        driver = self.drivers.get(discovery_type)
        LOG.info(_LI("Loaded discovery driver type: %s"), driver.obj)
        return driver


class ProvisioningManager(stevedore.named.NamedExtensionManager):
    """Manage provisioning drivers for BNP."""

    def __init__(self):
        # Mapping from provisioning driver name to DriverManager
        self.drivers = {}

        LOG.info(_LI("Configured provisioning driver names: %s"),
                 cfg.CONF.ml2_hpe.prov_driver)
        super(ProvisioningManager, self).__init__('bnp.prov_driver',
                                                  cfg.CONF.ml2_hpe.prov_driver,
                                                  invoke_on_load=True)
        LOG.info(_LI("Loaded provisioning driver names: %s"), self.names())
        self._register_provisioning()

    def _register_provisioning(self):
        for ext in self:
            provisioning_type = ext.obj.get_driver_name()
            if provisioning_type in self.drivers:
                LOG.error(_LE("provisioning driver '%(new_driver)s' ignored "
                              " provisioning driver '%(old_driver)s' already"
                              " registered for provisioning '%(type)s'"),
                          {'new_driver': ext.name,
                           'old_driver': self.drivers[provisioning_type].name,
                           'type': provisioning_type})
            else:
                self.drivers[provisioning_type] = ext
        LOG.info(_LI("Registered provisioning driver: %s"),
                 self.drivers.keys())

    def provisioning_driver(self, provisioning_type):
        """provisioning driver instance."""
        driver = self.drivers.get(provisioning_type)
        LOG.info(_LI("Loaded provisioning driver type: %s"), driver.obj)
        return driver
