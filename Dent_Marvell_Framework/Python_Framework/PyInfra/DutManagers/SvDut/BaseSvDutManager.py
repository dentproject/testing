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
from builtins import str
from builtins import range
from builtins import object
from abc import abstractmethod

from PyInfra.BaseTest_SV.SV_Enums.AppTypes import AppType
from PyInfra.DutManagers.SvDut.Types import SvBoard, DutChannelType, DutAppMode
from PyInfraCommon.BaseTest.BaseTestExceptions import TestCrashedException
from PyInfraCommon.ExternalImports.Communication import PyBaseComWrapper, PySerialComWrapper, PyTelnetComWrapper, \
    PySSHComWrapper
from PyInfraCommon.GlobalFunctions.IP import ping_till_timeout, poll_socket_till_timeout
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from time import sleep

class BaseSvDutManager(object):
    """
    base class that manages Dut that runs a  Software application
    """
    def __init__(self, dut_channel, testclass):
        self._dut_active_channel = dut_channel # type: PyBaseComWrapper
        self._dut_channels = {}  # type: dict[dut_channel_type:PyBaseComWrapper]
        if isinstance(dut_channel, PySerialComWrapper):
            self._dut_active_channel_type = DutChannelType.SERIAL
        elif isinstance(dut_channel,PyTelnetComWrapper):
            self._dut_active_channel_type = DutChannelType.TELNET
        elif isinstance(dut_channel,PySSHComWrapper):
            self._dut_active_channel_type = DutChannelType.SSH
        else:
            raise TypeError("BaseSvDutManager: cant determine dut channel type")
        from PyInfra.BaseTest_SV import BaseTest_SV
        self._testclassref = testclass  #type: BaseTest_SV
        self._sv_board = SvBoard()
        self.logger = testclass.logger
        self.PDU = BaseTest_SV._ConnectToPDU(self._testclassref)
        self.appMode = DutAppMode.Undefined
        self._ipaddr = None  # ip address for channel type telnet usage
        self._LUA_telnet_port = 12345
        self.appType = AppType.Undefined
        self.dut_prompt = "\n.*\s*#\s+"  # must be initlized to some regex pattern to described the prompt


    @abstractmethod
    def init_dut(self):
        """
        each derived class should implement something that init the dut on test start
        :return:
        :rtype:
        """
        pass

    @abstractmethod
    def login(self):
        """
        login to dut - must be implemented from derived classes
        :return:
        :rtype:
        """

    @abstractmethod
    def software_version(self):
        """
        each derived class should implement something that init the dut on test start
        :return:
        :rtype:
        """
        pass

    @abstractmethod
    def uboot_version(self):
        """
        login to dut - must be implemented from derived classes
        :return:
        :rtype:
        """

    def _set_active_channel(self, dut_channel):
        """
        sets the active communication channel in case it wasn't set at init or if need to swap channel
        for some actions
        :return:
        """
        if dut_channel:
            self._dut_active_channel = dut_channel
            for v in list(self._dut_channels.values()):
                if v == dut_channel:
                    for k in list(self._dut_channels.keys()):
                        if self._dut_channels[k] == v:
                            self._dut_active_channel_type = k
                            break
                    break

    def _add_channel(self, channel, channel_type):
        """
        adds the input channels to dictionary based on type of channel
        this api should be used given list of 2 channels 1 serial and 1 telnet
        and it registers the channel based on its type

        :param channel: channel to add
        :param channel_type: type of the channel
        :type channel: PyBaseComWrapper
        :type channel_type:DutChannelType
        :return: None
        """
        self._dut_channels[channel_type] = channel

    def _set_active_channel_by_type(self, channel_type):
        """
        tries to set active channel based on type of channel
        under the assumption that there is a channel of the requested type
        raises exception if not found
        :param channel_type: type of requested channel
        :type channel_type: DutChannelType
        :return:None
        """
        if channel_type in self._dut_channels:
            self._set_active_channel(self._dut_channels[channel_type])
        else:
            raise TestCrashedException(" there is not available channel of type {}".format(str(channel_type)))

    def _has_channel_type(self, channel_type):
        """
        :type channel_type: DutChannelType
        :param channel_type: type of requested channel
        :return: True if there is an available channel of the requested type
        :rtype: bool
        """
        return self._dut_channels.get(channel_type)

    def reboot(self, poll_dut_loaded=True, max_attempts=3, timeout_seconds=120, software_reset=True):
        """
        reboots the Dut by PDU if reboot mode is Hardware or by software reset if reboot mode is software
        :param poll_dut_loaded: if True polls the Dut by ping or by
        :param max_attempts: maximum attempts to try to reboot dut before giving up
        :param software_reset True if reset by is done by software, False otherwise
        :type poll_dut_loaded: bool
        :return: True if succeeded or false otherwise
        """
        funcname = GetFunctionName(self.reboot)
        try:
            reboot_func = self._software_reboot if software_reset else self._reboot_with_PDU
            for i in range(1, max_attempts + 1):
                if reboot_func(poll_dut_loaded, timeout_seconds=timeout_seconds):
                    if poll_dut_loaded:
                        if self.login():
                            return True
                        else:
                            wrn = funcname + "attempt #{} faild to connect to dut after reboot,retrying again for " \
                                             "up to {} more times".format(i, max_attempts + 1 - i)
                            self.logger.warning(wrn)
                    else:
                        return True

        except Exception as e:
            err = funcname + " failed to reboot Dut:{}".format(GetStackTraceOnException(e))
            self.logger.error(err)
        return False

    def telnet_login(self):
        result = False
        for i in range(3):
            result = self._dut_active_channel.SendCommandAndWaitForPattern(self._testclassref.DutSecondayChannel._userName, ExpectedPrompt="#")
            if result:
                break
            else:
                sleep(2)
        if self._testclassref.DutSecondayChannel._password:
            if "word" in self._dut_active_channel.lastBufferTillPrompt:
                self._dut_active_channel.SendCommandAndWaitForPattern(self._testclassref.DutSecondayChannel._password,
                                                                      ExpectedPrompt="#")
        if "#" not in self._dut_active_channel.lastBufferTillPrompt:
            raise Exception("Could not login to telnet channel")


    def _reboot_with_PDU(self, poll_dut_loaded=True, print_exceptions=False, timeout_seconds=20):
        """
        reboots the Dut with PDU
        :param poll_dut_loaded: polls the Dut has loaded back by either waiting for linux prompt with optionally ping test
        :type poll_dut_loaded:bool
        :param print_exceptions: if True will print exception that ocur
        :type print_exceptions:bool
        :return:True if dut loaded back and polling enabled (or True in polling is disabled)
        :rtype: bool
        """
        funcname = GetFunctionName(self._reboot_with_PDU)
        try:
            if self.PDU:
                if self._dut_active_channel_type is not DutChannelType.SERIAL:
                    self._dut_active_channel.Disconnect()
                self.PDU.reboot()
                if poll_dut_loaded:
                    if self._dut_active_channel_type in (DutChannelType.TELNET, DutChannelType.SSH):
                        if not ping_till_timeout(self._dut_active_channel._host, timeout=timeout_seconds,
                                                 initial_delay=10):
                            return False
                        port = 22 if self._dut_active_channel_type is DutChannelType.SSH else 23
                        return poll_socket_till_timeout(self._dut_active_channel._host, port, timeout=timeout_seconds)
                    else:
                        # wait for linux prompt using serial
                        return self._dut_active_channel.GetBufferTillPattern(ExpectedPrompt=self.dut_prompt,
                                                                             timeOutSeconds=timeout_seconds)
                else:
                    # no polling requested return immediately
                    return True
            else:
                err = funcname + "PDU is not available! please make sure you entered correct setting in your excel"
                self.logger.error(err)
        except Exception as ex:
            err = funcname + "caught exception:{}".format(GetStackTraceOnException(ex))
            if print_exceptions:
                self.logger.error(err)
        return False

    @abstractmethod
    def _software_reboot(self, poll_dut_loaded=True, print_exceptions=False, timeout_seconds=20):
        pass
