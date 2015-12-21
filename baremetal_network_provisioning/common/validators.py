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
# service type constants:

from simplejson import scanner as json_scanner
import webob.exc

from baremetal_network_provisioning.common import constants as const


def access_parameter_validator(data, valid_values=None):
    """Validate the access parameters."""
    if not data:
        # Access parameters must be provided.
        msg = _("Cannot create a switch from the given input.")
        return msg
    if type(data) is not dict:
        msg = _("Given details is not in the form of a dictionary.")
        return msg


def validate_request(request):
    """Validate if the request is in proper format."""
    try:
        body = request.json_body
    except json_scanner.JSONDecodeError:
        raise webob.exc.HTTPBadRequest(
            _("Invalid JSON body"))
    try:
        body = body.pop(const.BNP_SWITCH_RESOURCE_NAME)
    except KeyError:
        raise webob.exc.HTTPBadRequest(
            _("'switch' not found in request body"))
    return body


def validate_access_parameters(body):
    if body['access_protocol'].lower() not in const.SUPPORTED_PROTOCOLS:
        raise webob.exc.HTTPBadRequest(
            _("'access protocol %s' is not supported") % body[
                'access_protocol'])
    access_parameters = body.get("access_parameters")
    if body['access_protocol'].lower() == const.SNMP_V3:
        validate_snmpv3_parameters(access_parameters)
    else:
        validate_snmp_parameters(access_parameters)


def validate_snmp_parameters(access_parameters):
    """Validate SNMP v1 and v2c parameters."""
    if not access_parameters.get('write_community'):
        raise webob.exc.HTTPBadRequest(
            _("'write_community' not found in request body"))


def validate_snmpv3_parameters(access_parameters):
    """Validate SNMP v3 parameters."""
    if not access_parameters.get('security_name'):
        raise webob.exc.HTTPBadRequest(
            _("security_name not found in request body"))
    if access_parameters.get('auth_protocol'):
        if access_parameters.get('auth_protocol').lower(
        ) not in const.SUPPORTED_AUTH_PROTOCOLS:
            raise webob.exc.HTTPBadRequest(
                _("auth_protocol %s is not supported") %
                access_parameters['auth_protocol'])
        elif not access_parameters.get('auth_key'):
            raise webob.exc.HTTPBadRequest(
                _("auth_key is required for auth_protocol %s") %
                access_parameters['auth_protocol'])
        elif len(access_parameters.get('auth_key')) < 8:
            raise webob.exc.HTTPBadRequest(
                _("auth_key %s should be equal or more than"
                  "8 characters") % access_parameters['auth_key'])
    if access_parameters.get('priv_protocol'):
        if access_parameters.get('priv_protocol').lower(
        ) not in const.SUPPORTED_PRIV_PROTOCOLS:
            raise webob.exc.HTTPBadRequest(
                _("priv_protocol %s is not supported") %
                access_parameters['priv_protocol'])
        elif not access_parameters.get('priv_key'):
            raise webob.exc.HTTPBadRequest(
                _("priv_key is required for priv_protocol %s") %
                access_parameters['priv_protocol'])
        elif len(access_parameters.get('priv_key')) < 8:
            raise webob.exc.HTTPBadRequest(
                _("'priv_key %s' should be equal or more than"
                  "8 characters") % access_parameters['priv_key'])
