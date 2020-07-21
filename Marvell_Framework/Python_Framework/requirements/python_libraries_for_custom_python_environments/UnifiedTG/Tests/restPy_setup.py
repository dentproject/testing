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

from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.UTG import utg
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyTG import *
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyEnums import ixNetworkRestPyEnums
from ixnetwork_restpy.testplatform.sessions.ixnetwork.traffic.trafficitem.configelement.stack.field import field



vendorType = TGEnums.TG_TYPE.IxiaSSH
chas = '10.5.40.57'
serverHost1 = chas # = '127.0.0.1'
#serverHost1 = '10.5.232.47'

p1 = chas + '/3/5'
p2 = chas + '/3/6'
portsList = [p1 + ":" + p1, p2 + ":" + p2]
tg = utg.connect(vendorType, serverHost1, 'OlegK')  # type: ixNetworkRestPyTG
ixn_ports = tg.reserve_ports(portsList, clear=True, force=True)






vendorType = TGEnums.TG_TYPE.IxNetworkRestPy
serverHost1 = '127.0.0.1'
#serverHost1 = '10.5.232.47'
chas = '10.5.40.57'
p1 = chas + '/3/5'
p2 = chas + '/3/6'
portsList = [p1 + ":" + p1, p2 + ":" + p2]
tg = utg.connect(vendorType, serverHost1, 'restpy')  # type: ixNetworkRestPyTG
#1 Add 2 ports
# type: list[Port]
ixn_ports = tg.reserve_ports(portsList, clear=True, force=True)
txPort = ixn_ports[0]
rxPort = ixn_ports[1]

txPort.apply()
rxPort.apply()