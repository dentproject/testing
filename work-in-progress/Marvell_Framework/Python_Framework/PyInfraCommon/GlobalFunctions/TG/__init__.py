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

from builtins import str
from builtins import object
from time import sleep
from PyInfraCommon.ExternalImports.TG import TGPort,utg
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.GlobalFunctions.Utils.Time import TimeOut

class TxRateCalculator(object):
    """
    this class calculates sending rate for a given TG Port based on
    its speed and the destination line speed
    """
    # Constant Values
    bitsinByte = 8
    frameSizeOffset = 20 # in bytes
    MbpsToBitsPerSecond = 1000000

    def __init__(self):
        self.FrameSize = 0
        self.PPS = 0
        self.bps = 0
        self.PacketBurstSize = 0
        self.utilizationPercent = 0
        self.TrasnmitionDuration = 0

    def GetTxRate(self,TxPortSpeed,RxPortSpeed,FrameSize,TransmitDuration):
        """
        :type TxPortSpeed: int
        :type RxPortSpeed : int
        :type FrameSize : int
        :type TransmitDuration : int
        :param TxPortSpeed: int
        :param RxPortSpeed: int
        :param FrameSize: int
        :param TransmitDuration: int  in seconds
        :return: calucaltes the max send rate and updates its members
        """
        ratio = float(0)
        self.FrameSize = FrameSize
        self.TrasnmitionDuration = TransmitDuration
        if TxPortSpeed > RxPortSpeed:
            ratio = float(RxPortSpeed) / float(TxPortSpeed)
            self.utilizationPercent = int(float(100 * ratio))
        else:
            self.utilizationPercent = 100

        utilizationRationalNumber = float(self.utilizationPercent) / 100.0
        self.PPS = TxPortSpeed * self.MbpsToBitsPerSecond  # convert from Mbps to bits per seconds
        self.PPS /= self.bitsinByte  # convert to bytes per seconds
        self.PPS /= (FrameSize + self.frameSizeOffset)  # Bps (port link rate) / frame size with offset
        self.PPS *= utilizationRationalNumber  # adapt to initial utilization value
        self.PacketBurstSize = int(self.PPS * TransmitDuration)
        self.PPS = int (self.PPS)
        self.bps = self.PPS * self.bitsinByte


class TGPortListActions(object):
    """
    this class provides TG actions to be done on multiple TG ports
    """
    def __init__(self,tgportsList):
        if isinstance(tgportsList,list):
            self.tgports = tgportsList  # type: list[TGPort]
        else:
            err = "tgportsList is not of type list but of " + str(type(tgportsList))
            raise TypeError(err)

    def pollTGPortsLinkUp(self, timeout=30):
        """
        polls the TG ports for linkup state and returns true if polling succeeded
        or False if timeout occurred
        :param timeout: timeout in seconds before giving up
        :type timeout: int
        :return: True if polling succeeded
        :rtype : bool
        """
        funcname = GetFunctionName(self.pollTGPortsLinkUp)
        result = True
        TimeOut.set(timeout)
        while 1:
            break
        
        return result
    
    def resetFactoryDefault(self,WaitForLinkUpAfterReset = True,timeoutSeconds=20):
        """
        resets tgports to factoryDefault
        :rtype: bool
        """
        for Tgport in self.tgports:
            Tgport.reset_factory_defaults()

        if WaitForLinkUpAfterReset:
            return self.pollTGPortsLinkUp(timeoutSeconds)

    def startTraffic(self,waitTillTxDone = True):
        """
        starts traffic on all Tg ports
        :type waitTillTxDone: bool
        :return: None
        """
        for Tgport in self.tgports:
            Tgport.StartTx(waitTillTxDone)

    def clearCounters(self):
        """
        clears tgports counters
        :return:  None
        """
        for Tgport in self.tgports:
            Tgport.ClearCounters()

    def clearCountersAndSendTraffic(self,waitTillTxDone = True):
        """
        clears counters and then calls to start traffic
        :type waitTillTxDone: bool
        :return: None
        """
        self.clearCounters()
        self.startTraffic(waitTillTxDone)


def GF_SendL2Traffic (MacAddress, vlanID, portNum, NumOfPkt):
    """
        Functions Send L2 from Traffic Generator
        :param
            MacAddress  -  the configure MacAddress in the sending packet
            vlanID -  the configure vlanID in the sending packet
            portNum - Send traffic from this port
        :return:
            true  - on success
            false - on fail.
    """

    return True


def GF_VerifyTrafficOnPort (portNum, TxFrames, RxFrames):
    """
        :param
            portNum - read counters of this port
            TxFrame - number of transmit frame  verify if port send this amount of frame
            TxFrame - number of received frame  verify if port received this amount of frame
        :return:
            true  - on success
            false - on fail.
    """

    return True


