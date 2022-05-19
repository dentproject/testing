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

# Basic examples for using PowerDistributionUnit package
from PyInfraCommon.Managers.PowerDistributionUnit.PDUSocket import *
from PyInfraCommon.Managers.SNMP.SNMPTools import *


def testPdu():
    snmpV2Obj = SnmpManager.get(SnmpProtocolVersion.v2)
    snmpV2Obj('10.5.223.243', 'private', 'public')
    pduObj = PduSocket_SNMP(snmpV2Obj, 24)
    pduObj.reboot()

if __name__ == "__main__":
    testPdu()