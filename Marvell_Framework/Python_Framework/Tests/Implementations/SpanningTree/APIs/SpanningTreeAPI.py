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
from enum import Enum
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter
from CLI_GlobalFunctions.SwitchDev.SpanningTree.AbstractSpanningTreeConfig import AbstractSpanningTreeConfig
from Tests.Implementations.CommonTestAPI import CommonTestAPI


class RST_PORT_ROLE_PACKET(Enum):
    ALTERNATE_OR_BACKUP = '4'
    ROOT = '8'
    DESIGNATED = 'E'


timeToState = r"""

function check_stp_state() {{
  start_time=$(date +%s)
  while :; do
    stp_state=$({getStateCommand})
    curr_time=$(date +%s)
    duration=$((curr_time-start_time))
    echo $stp_state
    [[ $stp_state = $1 ]] && {{ echo got $stp_state state in $duration seconds; (brctl showstp {bridge} | awk -v RS='' '/{checkStatePort}/') 2>/dev/null; break; }} || sleep 1
    (("$duration" > $2)) && {{ echo Timeout of $2 seconds exceeded; exit 1; }}
  done
}}

echo Current time: $(date +%T)
check_stp_state {expectedState} {timeout}
echo Current time: $(date +%T)

"""


class SpanningTreeAPI(CommonTestAPI):

    def __init__(self, testClass):
        super(SpanningTreeAPI, self).__init__(testClass)

    def createAndSetSoftEntityUp(self, cleanupConfig=True, softEntity=None, **kwargs):
        if isinstance(softEntity, AbstractSpanningTreeConfig):
            self.Add_Cleanup_Function_To_Stack(softEntity.delete)
        super(SpanningTreeAPI, self).createAndSetSoftEntityUp(cleanupConfig, softEntity, **kwargs)

    def timeToState(self, bridge, checkStatePort, timeout, expectedState='forwarding', protocolVersion='00'):
        if protocolVersion == '00':
            getStateCommand = fr"ip -d -j -p link show {checkStatePort} | grep \"state\" | tr -d \"[[:space:],\,,\"]\"  | cut -d ':' -f 2"
        else:
            getStateCommand = f"mstpctl showportdetail {bridge} {checkStatePort} state"
        return GlobalGetterSetter().getter.execAsFile(timeToState.format(getStateCommand=getStateCommand,
                                                                         bridge=bridge,
                                                                         checkStatePort=checkStatePort,
                                                                         expectedState=expectedState,
                                                                         timeout=timeout),
                                                      getReturnCode=True)

    def stpStream(self, port, srcMac, rootBridge, protocolVId, rootPrio=32768, rootCost=0, bridgeId=None,
                  bridgePrio=32768, utilMode=TGEnums.STREAM_RATE_MODE.PACKETS_PER_SECOND, pps=0.5,
                  utilization=6.72e-007, maxAge=20,
                  portRole: RST_PORT_ROLE_PACKET = RST_PORT_ROLE_PACKET.DESIGNATED):

        def getHexRep(value, length):
            return f"{(length - len(hex(value)[2:])) * '0'}{hex(value)[2:]}"

        if bridgeId is None:
            bridgeId = srcMac.replace(':', '')
        rootPriority = getHexRep(rootPrio, 4)
        bridgePriority = getHexRep(bridgePrio, 4)

        return self.bridgedStream(port, src_mac=srcMac, dst_mac="01:80:C2:00:00:00", **{
            'packet.l2_proto': TGEnums.L2_PROTO.RAW,
            'packet.protocol_pad.enabled': True,
            'packet.protocol_pad.custom_data': f"4242030000{protocolVId * 2}7{portRole.value}{rootPriority}{rootBridge.replace(':', '')}"
                                               f"{getHexRep(rootCost, 8)}{bridgePriority}"
                                               f"{bridgeId}80020100{getHexRep(maxAge, 2)}0002000f00",
            'rate.mode': utilMode,
            'rate.pps_value': pps,
            'rate.utilization_value': utilization})
