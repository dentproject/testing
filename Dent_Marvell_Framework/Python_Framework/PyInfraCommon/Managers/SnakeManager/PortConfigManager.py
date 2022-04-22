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

from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger


class InterfaceInfo(object):
    def __init__(self, mode, speed, fec_mode, num_of_lanes):
        self.Mode = mode
        self.Speed = speed
        self.FecMode = fec_mode
        self.NumberOfLanes = num_of_lanes

    @property
    def Mode(self):
        return self._mode

    @Mode.setter
    def Mode(self, value):
        """
        :param value: Cpps Port Interface Mode enum
        :type value: CPSS_PORT_INTERFACE_MODE_ENT
        """
        if any(value == item.value for item in CPSS_PORT_INTERFACE_MODE_ENT):
            self._mode = value
        else:
            raise TypeError('Wrong cpss port interface mode. Should be from type CPSS_PORT_INTERFACE_MODE_ENT')

    @property
    def Speed(self):
        return self._speed

    @Speed.setter
    def Speed(self, value):
        """
        :param value: Cpps Port Speed enum
        :type value: CPSS_PORT_SPEED_ENT
        """
        if any(value == item.value for item in CPSS_PORT_SPEED_ENT):
            self._speed = value
        else:
            raise TypeError('Wrong cpss port speed. Should be from type CPSS_PORT_SPEED_ENT')

    @property
    def NumberOfLanes(self):
        return self._number_of_lanes

    @NumberOfLanes.setter
    def NumberOfLanes(self, value):
        """
        :param value: Number of lanes
        :type value: int
        """
        if isinstance(value, int):
            self._number_of_lanes = value
        else:
            raise TypeError('Wrong number of lanes value. Should be from type int')

    @property
    def FecMode(self):
        return self._fec_mode

    @FecMode.setter
    def FecMode(self, value):
        """
        :param value: Cpps Port Fec Mode enum
        :type value: CPSS_DXCH_PORT_FEC_MODE_ENT
        """
        if any(value == item.value for item in CPSS_DXCH_PORT_FEC_MODE_ENT):
            self._fec_mode = value
        else:
            raise TypeError('Wrong cpss port fec mode. Should be from type CPSS_DXCH_PORT_FEC_MODE_ENT')


class PortConfigManager(object):
    def __init__(self, list_of_pairs, num_of_lanes):
        self.Ports = list_of_pairs
        self.NumOfLanes = num_of_lanes
        self.ZippedPorts = []

    @property
    def Ports(self):
        return self._Pairs

    @Ports.setter
    def Ports(self, value):
        """
        :param value: List of tuples
        :type value: list
        """
        valid = True
        if isinstance(value, list):
            for item in value:
                if not (isinstance(item,object) and hasattr(item,"PortNum") or
                 isinstance(item, tuple) or len(item) != 2 or
                all( isinstance(p, int) or isinstance(p,object) and hasattr(p,"PortNum")  for p in item)):
                    valid = False
                    break

        if not valid:
            raise TypeError("Wrong list_of_pairs argument type. Should be a list of objects with PortNum property or"
                            "  paired tuples, format [(object, object), object]")
        else:
            self._Pairs = value
            # self._Pairs = self.SortPorts(value)

    @property
    def NumOfLanes(self):
        return self._NumOfLanes

    @NumOfLanes.setter
    def NumOfLanes(self, value):
        """
        :param value: Number of lanes used in this port mode/speed combination
        :type value: int
        """

        if not isinstance(value, int):
            raise TypeError("Wrong num_of_lanes argument type. Should be from type int.")
        else:
            self._NumOfLanes = value




    @classmethod
    def SortPorts(cls, ports):
        # self.Pairs.sort(key=lambda sElement: sElement[1].Port)
        # sort inner (inside tuples) pairs
        # i.e. before(0/8, 0/1), after sort (0/1, 0/8). When x/y: x-device, y-port.
        # self.Pairs = [(p[1], p[0]) if p[0].Port > p[1].Port else p for p in self.Pairs]

        func_name = GetFunctionName(cls.SortPorts)
        ports = [(p[1], p[0]) if isinstance(p, tuple) and p[0].PortNum > p[1].PortNum else p for p in ports]
        # sort list by Port id (1st in tuple), from lower to higher.
        #ports.sort(key=lambda sElement: sElement[0].PortNum if isinstance(sElement, tuple) else sElement.PortNum)
        #GlobalLogger.logger.info(func_name + " Sorted Pairs: {}".format(ports))
        return ports
        # key=lambda x: x.count,

    def ComputePorts(self):
        if self.NumOfLanes > 1:
            # solo - independent port, like Transmitter Loopback
            lp1, lp2, single = self.UnzipPorts()
            #len1 = len(single) - 1
            #devMask = [b.Port-a.Port for a, b in zip(single, single[1:])]
            #print "Deviation mask: {}".format(devMask)
            SinglePort_Blocks = []
            #block = ()
            # Given a single-port list, retrieve blocks (port members) suitable for number of lanes
            # i.e. Single-port list  [0/3, 0/6, 0/7, 0/14, 0/15, 0/16]
            # retrieved blocks [(0/6, 0/7), (0/14, 0/15)]
            # for indx, port in enumerate(single):
            #     if not block:
            #         block += (port,)
            #     elif port.Port - block[-1].Port == 1:
            #         block += (port,)
            #     else:
            #         block = (port,)
            #
            #     if len(block) == self.NumOfLanes:
            #         Blocks.append(block)
            #         block = ()
            SinglePort_Blocks, SinglePort_Leaders = self.__GatherPortsToBlocksAndLeaders(single)
            LinkPartner1_Blocks, LinkPartner1_Leaders = self.__GatherPortsToBlocksAndLeaders(lp1)
            LinkPartner2_Blocks, LinkPartner2_Leaders = self.__GatherPortsToBlocksAndLeaders(lp2)


            reportMsg = "Link Partner1 blocks: {}".format(LinkPartner1_Blocks)
            #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)
            reportMsg =  "Link Partner1 leaders: {}".format(LinkPartner1_Leaders)
            #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)

            reportMsg = "Link Partner2 blocks: {}".format(LinkPartner2_Blocks)
            #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)
            reportMsg = "Link Partner2 leaders: {}".format(LinkPartner2_Leaders)
            #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)

            reportMsg = "Single-port blocks: {}".format(SinglePort_Blocks)
            #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)
            reportMsg = "Single-port leaders: {}".format(SinglePort_Leaders)
            #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)
            # get the 1st port for the block, which represents the portId
            # blocks [(0/6, 0/7), (0/14, 0/15)]
            #singlePortLeaders = [b[0] for b in Blocks]


            # zip ports
            self.ZipPorts(LinkPartner1_Leaders, LinkPartner2_Leaders, SinglePort_Leaders)




            # for indx in range(0, len(single) - 2, 1):
            #     if not block:
            #         block = (single[indx],)
            #
            #     if devMask[indx] == 1:
            #         block += (single[indx+1],)
            #     else:
            #         block = (single[indx+1],)
            #
            #     if len(block) == self.NumOfLanes:
            #         classifiedSingle.append(block)
            #         block = ()

        else:
            self.ZippedPorts = self.Ports

        reportMsg = "Zipped Ports: {}".format(self.ZippedPorts)
        #GlobalLogger.logger.trace(reportMsg,onlyConsole=True)

    def __GatherPortsToBlocksAndLeaders(self, portList):
        # Given a single-port list, retrieve blocks (port members) suitable for number of lanes
        # i.e. Single-port list  [0/3, 0/6, 0/7, 0/14, 0/15, 0/16]
        # retrieved blocks [(0/6, 0/7), (0/14, 0/15)]
        # In addition the function returns the 1st port (port leaders) of the block, which represents the portId
        # I.e. For blocks [(0/6, 0/7), (0/14, 0/15)]
        # port leaders will be [0/6, 0/14]
        Blocks = []
        block = ()
        for indx, port in enumerate(portList):
            if not block or len(block) < self.NumOfLanes:
                block += (port,)
                if len(block) is len(portList) or indx + 1 is len(portList) :
                    Blocks.append(block)
            # elif port.PortNum - block[-1].PortNum == 1:
            #     block += (port,)
            # else:
            #     block = (port,)

            # if len(block) == self.NumOfLanes:
            else:
                Blocks.append(block)
                block = ()
                block += (port,)

        blockLeaders = [b[0] for b in Blocks]

        return Blocks, blockLeaders

    def ZipPorts(self, l1, l2, singlePorts):
        self.ZippedPorts = zip(l1, l2)
        self.ZippedPorts += singlePorts
        self.ZippedPorts = self.SortPorts(self.ZippedPorts)

    def UnzipPorts(self):
        linkPartner1 = []
        linkPartner2 = []
        single = []
        for item in self.Ports:
            if isinstance(item, tuple):
                linkPartner1.append(item[0])
                linkPartner2.append(item[1])
            else:
                single.append(item)

        reportMsg = "Link Partner 1: {}".format(linkPartner1)
        #GlobalLogger.logger.debug(reportMsg)
        reportMsg = "Link Partner 2: {}".format(linkPartner2)
        #GlobalLogger.logger.debug(reportMsg)
        reportMsg = "Single Port List: {}".format(single)
        #GlobalLogger.logger.debug(reportMsg)
        return linkPartner1, linkPartner2, single

    def GetMask(self, size):
        return [0] * size

    # def ComputePveLinks(self):
    #     result = []
    #     for i in range(0, len(self.Pairs), self.NumOfLanes):
    #         if i + self.NumOfLanes <= len(self.Pairs):
    #             self.ZippedPairs.append(self.Pairs[i])
    #
    #     print result


    def FindPort(self, port):
        result = None
        for indx, item in enumerate(self.Ports):
            if (isinstance(item, tuple) and port in item) or (isinstance(item, object) and item == port):
                result = indx
                break

        return result



                # def SortByTrafficSrcPort(self):
                #     for indx, item in enumerate(self.Pairs):
                #         if (isinstance(item, tuple) and self.SrcPort in item) or item == self.SrcPort:
                #             return indx

    @classmethod
    def DeployPorts(self, port_list):
        #return [p for item in self.ZippedPorts if isinstance(item, tuple) for p in item] + [p for item in
    # self.ZippedPorts]
        #[x + 1 if x >= 45 else x + 5 for x in l]
        new_list = []
        for item in port_list:
            if isinstance(item, tuple):
                for p in item:
                    new_list.append(p)
            else:
                new_list.append(item)

        return new_list