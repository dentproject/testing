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

from PyInfraCommon.ExternalImports.Communication import PyBaseComWrapper
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from .PortConfigManager import PortConfigManager, InterfaceInfo
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from enum import IntEnum,Enum

from PyInfraCommon.Globals.DutChannel.DutMainChannel import GlobalDutChannel


class TrafficInitiator(IntEnum):
    Unknown = 0
    TG_1 = 1
    TG_2 = 2
    CPU = 3

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name

class SnakeConfigurationmethod(Enum):
    Unknown = 0
    PVE = 1
    PipeRedirect = 2
    Vlan = 3
    Routing = 4
    VirtualRouting = 5


class SnakeSettings(object):
    """
    :type SnakeChainBreaker: CpssDutPort
    :type PveConfigurator: PVEConfigMultiplePortPairs
    """
    def __init__(self,channel,SnakeConfigMethod=SnakeConfigurationmethod.Unknown):
        self.SrcDstLinks = []
        self.SnakeChainBreaker = None
        self.channel = channel  # type: PyBaseComWrapper
        self.SnakeConfigMethod = SnakeConfigMethod


class SnakeManager(object):

    def __init__(self, traffic_initiator, traffic_src_port=None, traffic_dst_port=None, num_of_lanes=0,
                 channel=None,SnakeConfigMethod = SnakeConfigurationmethod.Unknown):
        """
        :param traffic_initiator: Traffic initiator - CPU, TG 1 port (TG_1) or TG 2 ports (TG_2)
        :type traffic_initiator: TrafficInitiator
        :param traffic_src_port: Traffic source port either CPU or TG, in case of TG list of all Tg source port Dut ports
        :type traffic_src_port: DutPort | list[DutPort]
        :param traffic_dst_port: Traffic destination port, used in only in case when traffic_initiator == TG_2
        list of all Tg source port Dut ports
        :type traffic_dst_port: DutPort | list[DutPort]
        :param channel: Communication channel reference
        :type channel: PyBaseComWrapper | None
        :param SnakeConfigMethod: the method that is used to create snake configuration
        :type SnakeConfigMethod:SnakeConfigurationmethod
        """

        if not channel:
            self.ComChannel = GlobalDutChannel.channel
        else:
            self.ComChannel = channel
        self.PortBlocks = []
        self.TrafficInitiator = traffic_initiator
        self.traffic_src_port_list = None
        self.traffic_dst_port_list = None
        self.TrafficSourcePort = traffic_src_port
        self.TrafficDestinationPort = traffic_dst_port
        self.num_of_lanes = num_of_lanes
        self.snake_config_method = SnakeConfigMethod
        self.SnakeSettings = SnakeSettings(self.ComChannel,SnakeConfigMethod)


    @property
    def TrafficSourcePort(self):
        return self._SrcPort

    @TrafficSourcePort.setter
    def TrafficSourcePort(self, value):
        """
        :param value: Traffic source port
        :type value: int
        """

        if not isinstance(value, object) or isinstance(value,object) and not hasattr(value,"PortNum"):
            raise TypeError("Wrong traffic_source_port argument type. Should be of type object with PortNum property.")
        else:
            if isinstance(value,object) and hasattr(value,"PortNum"):
                self._SrcPort = value
            elif isinstance(value,list):
                self.traffic_src_port_list = value
                self._SrcPort = value[0] # we always take the first port as traffic port

    @property
    def TrafficDestinationPort(self):
        return self._DstPort

    @TrafficDestinationPort.setter
    def TrafficDestinationPort(self, value):
        """
        :param value: Traffic destination port
        :type value: CpssDutPort | None
        """
        if not isinstance(value, object)  or isinstance(value,object) and not value is None and not hasattr(value,"PortNum") :
            raise TypeError("Wrong TrafficDestinationPort argument type. Should be of type object with PortNum property.")
        else:
            if isinstance(value,object) and hasattr(value,"PortNum"):
                self._DstPort = value.PortNum
            elif isinstance(value,list):
                self.traffic_src_port_list = value
                self._DstPort = value[0].PortNum  # we always take the first port as traffic port

    @property
    def TrafficInitiator(self):
        return self._TrafficInitiator

    @TrafficInitiator.setter
    def TrafficInitiator(self, value):
        """
        :param value: Traffic initiator TG or CPU
        :type value: TrafficInitiator
        """

        if not isinstance(value, TrafficInitiator):
            raise TypeError("Wrong traffic_initiator argument type. Should be from type CpssTrafficInitiator.")
        else:
            self._TrafficInitiator = value

    def AddPortList(self, list_of_pairs):
        # if not isinstance(interface_info, InterfaceInfo):
        #     raise TypeError("Wrong interface info argument type. Should be from type InterfaceInfo.")
        # pm = PortConfigManager(list_of_pairs, interface_info.NumberOfLanes)
        pm = PortConfigManager(list_of_pairs, self.num_of_lanes)
        pm.ComputePorts()
        self.PortBlocks.append(pm)

    def SetSrcDstLinks(self, ovveride_PveSrcDstPairs=None):
        funcname = GetFunctionName(self.SetSrcDstLinks)
        if not ovveride_PveSrcDstPairs:
            Blocks = []
            Blocks = self.PortBlocks
            Blocks.sort(key=lambda x: x.NumOfLanes)
            if self.TrafficInitiator == TrafficInitiator.CPU:
                # find source port and put it on in the 1st place in block
                #Blocks = [b.Ports for b in self.PortBlocks]
                # Blocks = []
                # Blocks = self.PortBlocks
                # Blocks.sort(key = lambda x: x.NumOfLanes)
                blockToPutInFirstPlace = 0
                for b_index, block in enumerate(Blocks):
                    indxSrcPort = block.FindPort(self.TrafficSourcePort)
                    if indxSrcPort is not None:
                        if isinstance(block.ZippedPorts[indxSrcPort], tuple):
                            if (self.TrafficSourcePort == block.ZippedPorts[indxSrcPort][1]):
                                tempList = list(block.ZippedPorts[indxSrcPort])
                                tempList[0], tempList[1] = tempList[1], tempList[0]
                                block.ZippedPorts[indxSrcPort] = tuple(tempList)
    
                            if indxSrcPort != 0:
                                block.ZippedPorts[0], block.ZippedPorts[indxSrcPort] = block.ZippedPorts[indxSrcPort], block.ZippedPorts[0]
    
                            blockToPutInFirstPlace = b_index
                        elif isinstance(block.ZippedPorts[indxSrcPort],object) and len(Blocks[0].Ports) == 1:
                            # single port
                            pair = (block.ZippedPorts[indxSrcPort],block.ZippedPorts[indxSrcPort])
                            block.ZippedPorts[indxSrcPort] = pair

                        break
    
                if blockToPutInFirstPlace != 0 and blockToPutInFirstPlace < len(Blocks):
                    Blocks[0], Blocks[blockToPutInFirstPlace] = Blocks[blockToPutInFirstPlace], Blocks[0]

            #for block in self.PortBlocks:
            allPorts = [p for b in Blocks for p in b.ZippedPorts]
            if self.TrafficInitiator == TrafficInitiator.TG_1:
                allPorts = [self.TrafficSourcePort] + allPorts
            elif self.TrafficInitiator == TrafficInitiator.TG_2:
                if self.TrafficDestinationPort is None:
                    raise ValueError(funcname+"Traffic destination port is None. Illegal for test with 2 TG ports.")
                else:
                    allPorts = [self.TrafficSourcePort] + allPorts + [self.TrafficDestinationPort]
            # reportMsg = "{}All ports in List: {}".format(funcname,allPorts)
            # GlobalLogger.logger.trace(reportMsg)
    
            self.__MakeSrcDstPairs(allPorts)
        else:
            self.SnakeSettings.SrcDstLinks = ovveride_PveSrcDstPairs
        reportMsg = "{} {} {} Pairs (Source,Destination) : {}"\
            .format(funcname,"Manually Set" if ovveride_PveSrcDstPairs else "", "PVE" if self.snake_config_method is SnakeConfigurationmethod.PVE else "Port Redirect" ,self.SnakeSettings.SrcDstLinks)
        GlobalLogger.logger.debug(reportMsg)
        # set PveConfigurator

    def __MakeSrcDstPairs(self, port_list):
        # if len(port_list) is 1:
        #     if isinstance(port_list[0], tuple):
        #         self.PveSettings.PveLinks.append()
        # PVE links from 1st to last
        for indx in range(0, len(port_list) - 1, 1):
        #for indx, val in enumerate(port_list):
            if isinstance(port_list[indx], tuple):
                if isinstance(port_list[indx + 1], tuple):
                    self.SnakeSettings.SrcDstLinks.append((port_list[indx][1], port_list[indx + 1][0]))
                else:
                    self.SnakeSettings.SrcDstLinks.append((port_list[indx][1], port_list[indx + 1]))
            else:
                if isinstance(port_list[indx + 1], tuple):
                    self.SnakeSettings.SrcDstLinks.append((port_list[indx], port_list[indx + 1][0]))
                else:
                    self.SnakeSettings.SrcDstLinks.append((port_list[indx], port_list[indx + 1]))

        if self.SnakeSettings.SnakeConfigMethod in (SnakeConfigurationmethod.PipeRedirect,SnakeConfigurationmethod.PVE):
            # PVE links from last to 1st
            reversed_port_list = [(item[1], item[0]) if isinstance(item,tuple) else item for item in port_list[::-1]]
            indx = 0
            rpl_len = len(reversed_port_list)
            remember_port = None
            #self.PveSettings.LastPortInChain = None
            while indx < rpl_len:
                # if there is a 'remembered' port on which the action should be done
                if remember_port:
                    if isinstance(reversed_port_list[indx], tuple):
                        self.SnakeSettings.SrcDstLinks.append((remember_port, reversed_port_list[indx][0]))
                        remember_port = reversed_port_list[indx][1]
                    # if we reached the last indx
                    elif indx == rpl_len - 1:
                        self.SnakeSettings.SrcDstLinks.append((remember_port, reversed_port_list[indx]))
                # if no ports were remembered for further action
                else:
                    if isinstance(reversed_port_list[indx], tuple):
                        remember_port = reversed_port_list[indx][1]
                    elif indx == 0: # the 1st index
                        remember_port = reversed_port_list[indx]
                        # chain breaker

                indx += 1

            # PVE links from dst to src (vice versa) - don't use
            #reversed_pve_links = [(y, x) for x, y in self.PveSettings.PveLinks[::-1]]
            #self.PveSettings.PveLinks.extend(reversed_pve_links)

            # 1st and last ports in the port list
            #self.PveSettings.FirstPortInChain = port_list[0][0] if isinstance(port_list[0], tuple) else port_list[0]
            first_port_in_port_list = port_list[0][0] if isinstance(port_list[0], tuple) else port_list[0]
            last_port_in_port_list = port_list[-1][1] if isinstance(port_list[-1], tuple) else port_list[-1]

            # 1st and last ports in PVE chain
            #self.PveSettings.FirstPortInChain = self.PveSettings.PveLinks[-1][1]
            #self.PveSettings.LastPortInChain = self.PveSettings.PveLinks[-1][0]

            # PVE chain breaker
            if self.SnakeSettings.SrcDstLinks:
                self.SnakeSettings.SnakeChainBreaker = self.SnakeSettings.SrcDstLinks[-1][0]

            # Bind the PVE chain edges
            if self.TrafficInitiator == TrafficInitiator.TG_1:
                # if last port is a tuple
                if isinstance(port_list[-1], tuple):
                    # bind last port to itself
                    self.SnakeSettings.SrcDstLinks.append((last_port_in_port_list, last_port_in_port_list))
            elif self.TrafficInitiator == TrafficInitiator.CPU:
                # if 1st port is a tuple
                if isinstance(port_list[0], tuple):
                    # bind 1st port to itself
                    self.SnakeSettings.SrcDstLinks.append((first_port_in_port_list, first_port_in_port_list))
                    # update PVE chain breaker
                    self.SnakeSettings.SnakeChainBreaker = first_port_in_port_list

                # if last port is a tuple
                if isinstance(port_list[-1], tuple):
                    # bind last port to itself
                    self.SnakeSettings.SrcDstLinks.append((last_port_in_port_list, last_port_in_port_list))










