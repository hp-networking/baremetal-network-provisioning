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


import abc

import six


@six.add_metaclass(abc.ABCMeta)
class DiscoveryDriverAPI(object):
    """Interface for back-end discovery drivers."""

    def initialize(self):
        pass

    @abc.abstractmethod
    def discover_switch(self, switch_info):
        """discover_switch discovers the physical switch and ports."""
        pass

    @abc.abstractmethod
    def get_ports_status(self, switch_info):
        """get_ports_status gets the operation status of the ports."""
        pass

    @abc.abstractmethod
    def get_driver_name(self):
        """get driver name to load the driver."""
        pass
