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

from neutron.plugins.ml2 import driver_api as api

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class BNPExtensionDriver(api.ExtensionDriver):
    _supported_extension_aliases = ["switch"]

    def initialize(self):
        LOG.info(_("BNPExtensionDriver initialization complete"))

    @property
    def extension_alias(self):
        """
        Supported extension alias.

        :returns: alias identifying the core API extension supported
                  by this BNP driver
        """
        if not hasattr(self, '_aliases'):
            aliases = self._supported_extension_aliases[:]
            self._aliases = aliases
        return self._aliases
