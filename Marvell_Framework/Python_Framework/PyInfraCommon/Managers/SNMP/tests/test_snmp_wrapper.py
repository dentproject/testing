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

from __future__ import print_function
# Basic examples for using SNMP wrapper package

from builtins import input
from PyInfraCommon.Managers.SNMP.SNMPTools import *

def TestSnmpV2():
    # OIDs
    resetAldrinOid = (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 11, 1, 1, 24) # reset port 24
    outletStatusOid = (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 5, 1, 1, 24) # port 24 status
    # snmp object initializator
    snmpV2Obj = SnmpManager.get(SnmpProtocolVersion.v2)
    snmpV2Obj('10.5.223.243', 'private', 'public')
    #get example
    results = []
    results = snmpV2Obj.Get(outletStatusOid)
    # snmp value type
    print("Get result (SNMP value type):{}, type {}".format(results[0], type(results[0])))
    # python native value type
    temp = SnmpVal2Native(results[0])
    print("Get result (python native value type):{}, type {}".format(temp, type(temp)))
    #set example
    snmpV2Obj.Set(resetAldrinOid, 3)


def TestSnmpV3():
    ##OIDs
    resetAldrinOid = (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 11, 1, 1, 24)  # reset port 24
    outletStatusOid = (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 5, 1, 1, 24)  # port 24 status
    # snmp object initializator
    snmpV3Obj = SnmpManager.get(SnmpProtocolVersion.v3)
    snmpV3Obj.SetTrasnportLayerParams('10.5.223.243')
    snmpV3Obj.SetSecurityData('stasok1', 'password123', None, USMAuthProtocol.usm_MD5)
    # get example
    results = []
    results = snmpV3Obj.Get(outletStatusOid)
    # snmp value type
    print("Get result (SNMP value type):{}, type {}".format(results[0], type(results[0])))
    # python native value type
    temp = SnmpVal2Native(results[0])
    print("Get result (python native value type):{}, type {}".format(temp, type(temp)))
    # set example
    snmpV3Obj.Set(resetAldrinOid, 3)

if __name__ == "__main__":
    try:
        #TestSnmpV2()
        TestSnmpV3()
    except SNMPToolError as e:
        print(str(e))

    eval(input("Press Enter to continue..."))