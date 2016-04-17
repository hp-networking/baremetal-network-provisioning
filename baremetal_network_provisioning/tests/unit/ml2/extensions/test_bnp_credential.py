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

from baremetal_network_provisioning.db import bm_nw_provision_db as db
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

    def _test_create_credential_for_snmp(self, body, cred_name):
        create_req = self.new_create_request('bnp-credentials', body,
                                             'json')
        with contextlib.nested(
            mock.patch.object(db, 'get_snmp_cred_by_name',
                              return_value=cred_name),
                mock.patch.object(db, 'add_bnp_snmp_cred')):
            self.bnp_wsgi_controller.create(create_req)
            db.get_snmp_cred_by_name.called
            db.add_bnp_snmp_cred.called

    def _test_create_credential_for_netconf(self, body, cred_name):
        create_req = self.new_create_request('bnp-credentials', body,
                                             'json')
        with contextlib.nested(
            mock.patch.object(os.path, 'isfile', return_value=True),
            mock.patch.object(db, 'get_netconf_cred_by_name',
                              return_value=cred_name),
                mock.patch.object(db, 'add_bnp_netconf_cred')):
            self.bnp_wsgi_controller.create(create_req)
            os.path.isfile.called
            db.get_netconf_cred_by_name.called
            db.add_bnp_netconf_cred.called

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
        result_snmpv3 = self._test_create_credential_for_snmp(body_snmpv3,
                                                              None)
        result_snmpv1 = self._test_create_credential_for_snmp(body_snmpv1,
                                                              None)
        result_snmpv2c = self._test_create_credential_for_snmp(body_snmpv2c,
                                                               None)
        self.assertEqual(None, result_snmpv3)
        self.assertEqual(None, result_snmpv1)
        self.assertEqual(None, result_snmpv2c)

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
        result_netssh = self._test_create_credential_for_netconf(body_netssh,
                                                                 None)
        result_netsoap = self._test_create_credential_for_netconf(body_netsoap,
                                                                  None)
        result_netsoap = self._test_create_credential_for_netconf(body_netsoap,
                                                                  None)
        self.assertEqual(None, result_netssh)
        self.assertEqual(None, result_netsoap)

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
                          body_snmp, None)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netconf, None)

    def test_create_cred_with_existing_name(self):
        body_snmp = {"bnp_credential":
                     {"name": "CRED1",
                      "snmpv1":
                      {"write_community": "public"}}}
        body_netconf = {"bnp_credential":
                        {"name": "CRED2",
                         "netconf-ssh":
                         {"key_path": "/home/fakedir/key1.rsa"}}}
        self.assertRaises(webob.exc.HTTPConflict,
                          self._test_create_credential_for_snmp,
                          body_snmp, 'CRED1')
        self.assertRaises(webob.exc.HTTPConflict,
                          self._test_create_credential_for_netconf,
                          body_netconf, 'CRED2')

    def test_create_cred_with_no_name(self):
        body_snmp = {"bnp_credential":
                     {"snmpv2c":
                      {"write_community": "public"}}}
        body_netconf = {"bnp_credential":
                        {"netconf-ssh":
                         {"key_path": "/home/fakedir/key1.rsa"}}}
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_snmp,
                          body_snmp, None)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netconf, None)

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
                          body_snmpv2, None)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_snmp,
                          body_snmpv3, None)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netssh, None)
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self._test_create_credential_for_netconf,
                          body_netsoap, None)
