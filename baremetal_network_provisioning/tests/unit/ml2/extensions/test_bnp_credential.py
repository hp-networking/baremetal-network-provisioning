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

from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit import testlib_api

from baremetal_network_provisioning.ml2.extensions import bnp_credential

import os.path

import mock
import webob.exc

import contextlib


class TestBnpCredential(test_plugin.NeutronDbPluginV2TestCase,
                        testlib_api.WebTestCase):

    def setUp(self):
        super(TestBnpCredential, self).setUp()
        self.bnp_wsgi_controller = bnp_credential.BNPCredentialController()

    def _test_create_credential_for_snmp(self, body):
        create_req = self.new_create_request('bnp-credentials', body,
                                             'json')
        return self.bnp_wsgi_controller.create(create_req)

    def _test_create_credential_for_netconf(self, body):
        create_req = self.new_create_request('bnp-credentials', body,
                                             'json')
        with contextlib.nested(
                mock.patch.object(os.path, 'isfile', return_value=True)):
            result = self.bnp_wsgi_controller.create(create_req)
            os.path.isfile.called
            return result

    def test_create_valid_cred_for_snmp(self):
        body_snmpv3 = {"bnp_credential":
                       {"name": "CRED1",
                        "snmpv3":
                        {"security_name": "xyz",
                         "auth_protocol": "md5",
                         "auth_key": "abcd1234",
                         "priv_protocol": "des",
                         "priv_key": "dummy_key"}}}
        body_snmpv1 = {"bnp_credential":
                       {"name": "CRED2",
                        "snmpv1":
                        {"write_community": "public"}}}
        body_snmpv2c = {"bnp_credential":
                        {"name": "CRED3",
                         "snmpv2c":
                         {"write_community": "public"}}}
        result_snmpv3 = self._test_create_credential_for_snmp(body_snmpv3)
        result_snmpv1 = self._test_create_credential_for_snmp(body_snmpv1)
        result_snmpv2c = self._test_create_credential_for_snmp(body_snmpv2c)
        self.assertEqual(result_snmpv3['bnp_credential']['name'],
                         body_snmpv3['bnp_credential']['name'])
        self.assertEqual(result_snmpv1['bnp_credential']['name'],
                         body_snmpv1['bnp_credential']['name'])
        self.assertEqual(result_snmpv2c['bnp_credential']['name'],
                         body_snmpv2c['bnp_credential']['name'])

    def test_create_valid_cred_for_netconf(self):
        body_netssh = {"bnp_credential":
                       {"name": "CRED1",
                        "netconf-ssh":
                        {"key_path": "/home/fakedir/key1.rsa"}}}
        body_netsoap = {"bnp_credential":
                        {"name": "CRED2",
                         "netconf-soap":
                         {"user_name": "fake_user",
                          "password": "fake_password"}}}
        result_netssh = self._test_create_credential_for_netconf(body_netssh)
        result_netsoap = self._test_create_credential_for_netconf(body_netsoap)
        self.assertEqual(result_netssh['bnp_credential']['name'],
                         body_netssh['bnp_credential']['name'])
        self.assertEqual(result_netsoap['bnp_credential']['name'],
                         body_netsoap['bnp_credential']['name'])

    def test_create_cred_with_invalid_protocol(self):
        body_snmp = {"bnp_credential":
                     {"name": "CRED1",
                      "snmpv4":
                      {"write_community": "public"}}}
        body_netconf = {"bnp_credential":
                        {"name": "CRED2",
                         "netconf-abc":
                         {"key_path": "/home/fakedir/key1.rsa"}}}
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_snmp,
                          body_snmp)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netconf)

    def test_create_cred_with_existing_name(self):
        body_snmp = {"bnp_credential":
                     {"name": "CRED1",
                      "snmpv1":
                      {"write_community": "public"}}}
        body_netconf = {"bnp_credential":
                        {"name": "CRED2",
                         "netconf-ssh":
                         {"key_path": "/home/fakedir/key1.rsa"}}}
        self._test_create_credential_for_snmp(body_snmp)
        self.assertRaises(webob.exc.HTTPConflict,
                          self._test_create_credential_for_snmp,
                          body_snmp)
        self._test_create_credential_for_netconf(body_netconf)
        self.assertRaises(webob.exc.HTTPConflict,
                          self._test_create_credential_for_netconf,
                          body_netconf)

    def test_create_cred_with_no_name(self):
        body_snmp = {"bnp_credential":
                     {"snmpv2c":
                      {"write_community": "public"}}}
        body_netconf = {"bnp_credential":
                        {"netconf-ssh":
                         {"key_path": "/home/fakedir/key1.rsa"}}}
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_snmp,
                          body_snmp)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netconf)

    def test_create_cred_with_invalid_parameters(self):
        body_snmpv2 = {"bnp_credential":
                       {"name": "CRED1",
                        "snmpv2c":
                        {"write_community": "public",
                         "fake_key": "/home/fakedir/key1.rsa"}}}
        body_snmpv3 = {"bnp_credential":
                       {"name": "CRED2",
                        "snmpv3":
                        {"security_name": "xyz",
                         "auth_protocol": "md5",
                         "priv_protocol": "des",
                         "priv_key": "dummy_key"}}}
        body_netssh = {"bnp_credential":
                       {"name": "CRED3",
                        "fake_key": "fake_value",
                        "netconf-ssh":
                        {"key_path": "/home/fakedir/key1.rsa"}}}
        body_netsoap = {"bnp_credential":
                        {"name": "CRED4",
                         "netconf-soap":
                         {"user_name": "fake_user"}}}
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_snmp,
                          body_snmpv2)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_snmp,
                          body_snmpv3)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netssh)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netsoap)
