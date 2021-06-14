###################################################################################
#	Marvell GPL License
#	
#	If you received this File from Marvell, you may opt to use, redistribute and/or
#	modify this File in accordance with the terms and conditions of the General
#	Public License Version 2, June 1991 (the "GPL License"), a copy of which is
#	available along with the File in the license.txt file or by writing to the Free
#	Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 or
#	on the worldwide web at http://www.gnu.org/licenses/gpl.txt.
#	
#	THE FILE IS DISTRIBUTED AS-IS, WITHOUT WARRANTY OF ANY KIND, AND THE IMPLIED
#	WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE ARE EXPRESSLY
#	DISCLAIMED.  The GPL License provides additional details about this warranty
#	disclaimer.
###################################################################################


"""
%%OpenSourceCode_License_Start%%
%%License%% Apache License 2.0
%%LicenseLink%% http://www.apache.org/licenses/LICENSE-2.0
%%Authors%% https://github.com/ogenstad
%%CodeReference%% https://github.com/networklore/nelsnmp/blob/master/lib/nelsnmp/
%%ImplementedIn%% TYPES, SnmpVal2Native, NativeVal2Snmp
%%Description%%
Code adapted from Github project:
https://github.com/networklore/nelsnmp
(Source: https://github.com/networklore/nelsnmp/blob/master/lib/nelsnmp/snmp.py retrieved in Sep 2017)

Copyright 2015 Patrick Ogenstad <patrick@ogenstad.com>
Modified 2017

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
%%OpenSourceCode_License_End%%
"""

from builtins import str
from pysnmp.proto.api import v2c
from datetime import timedelta
import socket

TYPES = {
    'Integer': v2c.Integer,
    'Integer32': v2c.Integer32,
    'Unsigned32': v2c.Unsigned32,
    'Counter32': v2c.Counter32,
    'Counter64': v2c.Counter64,
    'Gauge32': v2c.Gauge32,
    'TimeTicks': v2c.TimeTicks,
    'IpAddress': v2c.IpAddress,
    'OctetString': v2c.OctetString,
}

def SnmpVal2Native(snmpVal):
    """
    :param snmpVal: value received from SNMP Get command
    :return: The native value corresponding to snmpVal
    """
    if isinstance(snmpVal, v2c.Integer):
        result = int(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.Integer32):
        result = int(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.Unsigned32):
        result = int(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.Counter32):
        result = int(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.Counter64):
        result = int(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.Gauge32):
        result = int(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.TimeTicks):
        result = timedelta(seconds=int(snmpVal.prettyPrint()) / 100.0)
    elif isinstance(snmpVal, v2c.IpAddress):
        result = str(snmpVal.prettyPrint())
    elif isinstance(snmpVal, v2c.OctetString):
        try:
            result = snmpVal.asOctets().decode(snmpVal.encoding)
        except UnicodeDecodeError:
            return snmpVal.asOctets()
    else:
        result = snmpVal
    return result


def NativeVal2Snmp(nativeVal, snmpValueType):
    """
    :param nativeVal: native for python values, i.e. int/float/str etc.
    :return: The SNMP suitable value
    """
    if snmpValueType is None:
        # Try to autodetect desired SNMP value type
        if isinstance(nativeVal, int):
            result = v2c.Integer(nativeVal)
        elif isinstance(nativeVal, float):
            result = v2c.Integer(nativeVal)
        elif isinstance(nativeVal, str):
            if IsValidIpv4Address(nativeVal):
                result = v2c.IpAddress(nativeVal)
            else:
                result = v2c.OctetString(nativeVal)
        else:
            raise TypeError(
                "Unable to autodetect SNMP value type. Please supply "
                "the snmpValueType argument."
                ", ".join(list(TYPES.keys()))
            )
    else:
        if snmpValueType not in TYPES:
            raise ValueError("'{}' is not one of the supported types: {}".format(
                snmpValueType,
                ", ".join(list(TYPES.keys()))
            ))

        result = TYPES[snmpValueType](nativeVal)
    return result


"""
%%OpenSourceCode_License_Start%%
%%License%% CC-Wiki
%%LicenseLink%% https://creativecommons.org/licenses/by-sa/3.0/
%%Authors%% https://stackoverflow.com/users/6899/tzot; https://stackoverflow.com/users/284318/danilo-bargen
%%CodeReference%% https://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
%%ImplementedIn%% IsValidIpv4Address; IsValidIpv6Address
%%Description%% 
Code adapted from StackOverflow page "How to validate IP address in Python? [duplicate]":
https://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
Authors: https://stackoverflow.com/users/6899/tzot, https://stackoverflow.com/users/284318/danilo-bargen
For copyright and licensing information, please visit: https://creativecommons.org/licenses/by-sa/3.0/
%%OpenSourceCode_License_End%%
"""


def IsValidIpv4Address(ip_address):
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
    except AttributeError:  # no inet_pton here
        try:
            socket.inet_aton(ip_address)
        except socket.error:
            return False
        return ip_address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def IsValidIpv6Address(ip_address):
    try:
        socket.inet_pton(socket.AF_INET6, ip_address)
    except socket.error:  # not a valid address
        return False
    return True

