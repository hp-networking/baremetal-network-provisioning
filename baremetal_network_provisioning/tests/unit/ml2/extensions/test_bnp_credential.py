# Copyright (c) 2014 OpenStack Foundation.
# (c) Copyright [2016] Hewlett-Packard Enterprise Development Company, L.P.
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

from neutron.api import extensions
from neutron.common import config
import neutron.extensions
from neutron.plugins.ml2 import config as ml2_config
from neutron.tests.unit.api.v2 import test_base
from neutron.tests.unit.db import test_db_base_plugin_v2 as test_plugin
from neutron.tests.unit import testlib_api
from baremetal_network_provisioning.db import bm_nw_provision_models as models
from baremetal_network_provisioning.db import bm_nw_provision_db as db
from baremetal_network_provisioning.drivers import discovery_driver
from baremetal_network_provisioning.ml2.extensions import bnp_credential
from baremetal_network_provisioning.common import validators

import mock
import webob.exc

import contextlib


TARGET_PLUGIN = 'neutron.plugins.ml2.plugin.Ml2Plugin'
_get_path = test_base._get_path
extensions_path = ':'.join(neutron.extensions.__path__)




class TestBnpCredential(test_plugin.NeutronDbPluginV2TestCase,
                      testlib_api.WebTestCase):

    fmt = 'json'
    _mechanism_drivers = ['hpe_bnp']
    _ext_drivers = 'bnp_ext_driver'

    def setUp(self):
        super(TestBnpCredential, self).setUp()
        self.setup_coreplugin(TARGET_PLUGIN)
        ext_mgr = extensions.PluginAwareExtensionManager.get_instance()
        ml2_config.cfg.CONF.set_override('extension_drivers',
                                         self._ext_drivers,
                                         group='ml2')
        ml2_config.cfg.CONF.set_override('mechanism_drivers',
                                         self._mechanism_drivers,
                                         group='ml2')
        app = config.load_paste_app('extensions_test_app')
        self.ext_api = extensions.ExtensionMiddleware(app, ext_mgr=ext_mgr)
        self.bnp_wsgi_controller = bnp_credential.BNPCredentialController()

       
       
        self.snmp_req1 = {"bnp_credential":
                          {"name": "CRED1",
                           "snmpv3":
                            {"security_name": "phani",
                             "auth_protocol": "md5",
                             "auth_key": "abcd1234",
                             "priv_protocol": "des",
                             "priv_key": "xxxxxxxx"}}}
       
        self.snmp_body1 = {"name": "CRED1",
                           "snmpv3":
                            {"security_name": "phani",
                             "auth_protocol": "md5",
                             "auth_key": "abcd1234",
                             "priv_protocol": "des",
                             "priv_key": "xxxxxxxx"}}
        

        self.netconf_req1 = {"bnp_credential":
                              {"name": "CRED4",
                               "netconf-ssh":
                                {"key_path": "/home/sdn/key2.rsa"}}}
        
        self.netconf_body1 =  {"name": "CRED4",
                               "netconf-ssh":
                                {"key_path": "/home/sdn/key2.rsa"}}

        self.dbval=models.BNPSNMPCredential(
            id='123',
            name='CRED1',
            proto_type='snmpv3',
            security_name='phani',
            auth_protocol='md5',
            auth_key='abcd1234',
            priv_protocol= 'des',
            priv_key='xxxxxxxx',
            security_level=None)
        
        self.dbval1=models.BNPNETCONFCredential(
            id='123',
            name='CRED4',
            proto_type='netconf-ssh',
            key_path= "/home/sdn/key2.rsa")
        
        self.protoval='snmpv3'
        self.protoval1='netconf-ssh'
        
        
    
    def _create_credentials_for_snmp(self,req,name,dbval,protoval,body):
        create_req = self.new_create_request('bnp-credentials',req, 'json')
        with contextlib.nested(
            mock.patch.object(validators, 'validate_access_parameters',
                              return_value=protoval),
            mock.patch.object(self.bnp_wsgi_controller, '_create_snmp_creds',
                              return_value=self._create_snmp_cred(body,name,dbval,protoval))):
            result = self.bnp_wsgi_controller.create(create_req)
        
        
    def _create_snmp_cred(self,body,ret,dbval,protoval):
        fake_context = mock.Mock()
        with contextlib.nested(
            mock.patch.object(db, 'get_snmp_cred_by_name',return_value=ret),
            mock.patch.object(db, 'add_bnp_snmp_cred',return_value=dbval)):
            db.get_snmp_cred_by_name.called
            db.add_bnp_snmp_cred.called
            return self.bnp_wsgi_controller._create_snmp_creds(fake_context,body,protoval)
        
    def _create_credentials_for_netconf(self,req,name,dbval,protoval,body):
        create_req = self.new_create_request('bnp-credentials',req, 'json')
        with contextlib.nested(
            mock.patch.object(validators, 'validate_access_parameters',
                              return_value=protoval),
            mock.patch.object(self.bnp_wsgi_controller, '_create_netconf_creds',
                              return_value=self._create_netconf_cred(body,name,dbval,protoval))):
            result = self.bnp_wsgi_controller.create(create_req)
        
        
    def _create_netconf_cred(self,body,ret,dbval,protoval):
        fake_context = mock.Mock()
        with contextlib.nested(
            mock.patch.object(db, 'get_netconf_cred_by_name',return_value=ret),
            mock.patch.object(db, 'add_bnp_netconf_cred',return_value=dbval)):
            db.get_netconf_cred_by_name.called
            db.add_bnp_netconf_cred.called
            return self.bnp_wsgi_controller._create_netconf_creds(fake_context,body,protoval)
        
        
        
    def test_create_snmp_credentials_with_existing_name(self):
        self._create_credentials_for_snmp(self.snmp_req1,None,self.dbval,self.protoval,self.snmp_body1)
        self.assertRaises(webob.exc.HTTPConflict,self._create_credentials_for_snmp,
                          self.snmp_req1,'123',self.dbval,self.protoval,self.snmp_body1)
        
       
        
    def test_create_netconf_credentials_with_existing_name(self):
        self._create_credentials_for_netconf(self.netconf_req1,None,self.dbval1,self.protoval1,self.netconf_body1)
        self.assertRaises(webob.exc.HTTPConflict,self._create_credentials_for_netconf,
                          self.netconf_req1,'123',self.dbval1,self.protoval1,self.netconf_body1)
        
    def test_create_snmp_credentials_with_invalid_protocol(self):
        req2= {"bnp_credential":
               {"name": "CRED1",
                "snmpv4":
                 {"security_name": "phani",
                  "auth_protocol": "md5",
                  "auth_key": "abcd1234",
                  "priv_protocol": "des",
                  "priv_key": "xxxxxxxx"}}}
        self.assertRaises(webob.exc.HTTPBadRequest,self._create_credentials_for_snmp,
                          req2,None,self.dbval,self.protoval,self.snmp_body1)
        
    def test_create_netconf_credentials_with_invalid_protocol(self):
        req2= {"bnp_credential":
               {"name": "CRED4",
                "netconf-abc":
                {"key_path": "/home/sdn/key2.rsa"}}}
        self.assertRaises(webob.exc.HTTPBadRequest,self._create_credentials_for_netconf,
                          req2,None,self.dbval1,self.protoval1,self.netconf_body1)
        
        
    
        
        
        
        
   
        
    
            
            
            
    
            


             


