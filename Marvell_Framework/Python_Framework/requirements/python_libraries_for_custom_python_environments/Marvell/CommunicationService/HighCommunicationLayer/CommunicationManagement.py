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

# from ..CoSCommunicationAlgoLayer.CoSCommunicationAlgo import *
from builtins import str
from builtins import object
from ..PyCommunicationAlgoLayer.PyCommunicationAlgo import *
from ..CommunicationExceptions.Exceptions import *
# from Communication.Exceptions import *
from ..CommunicationUtilitiesLayer.CommunicationUtilities import *

# == Commmunication Managment ==

"""
Generic Communication API .
its support the bellow algorithms.
Note : The system support multi-communication in parallel
"""


class CommunicationManagement(object):
    connectedChannels = dict()

    @staticmethod
    def Connect(commType, port, ipAddr=None, uname=None, password=None, prompt=">", **extraParameters):
        """connect the device

         commType: communication type - see [Types.py]

         port: port id (integer)

         ipAddr: ip address with ip4 format (e.g 00.00.00.00)

         uname: user name , None in default

         password: password , None in default

         prompt: ">" in default

        :return: connection alias if connected successful,otherwise return None
        """
        m_commAlgo = None

        # To support running from the Web Service

        if not isinstance(commType, CommunicationType):
            commType = CommunicationType(commType)

        # end

        connAlias = CommunicationManagement.createExpectedAlias(commType, port, ipAddr, uname, **extraParameters)

        if CommunicationManagement.is_connected(connAlias):
            return connAlias

        m_commAlgo = CommunicationManagement.getCommunicationAlgo(prompt=prompt)

        connAlias = m_commAlgo.Connect(commType, port, ipAddr=ipAddr, uname=uname, password=password, **extraParameters)

        CommunicationManagement.addToConnectionChannelDict(connAlias, m_commAlgo)

        return connAlias

    @staticmethod
    def Disconnect(connectionAlias):
        """disconnect channel connection
        connectionAlias : connection Alias
        """
        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)
        m_commAlgo.Disconnect()
        CommunicationManagement.removeFromConnectionChannelDict(connectionAlias)

    @staticmethod
    def RegisterChannelEventsCallBack(connectionAlias, callBackId, connectionEventsCallBack):
        if not CommunicationManagement.is_connected(connectionAlias):
            raise PythonComException("Channel not connected or channel alias is invalid, "
                                     "make sure to pass valid channel Alias !")

        print("register call back {} of connection {}".format(callBackId,str(connectionAlias)))

        CommunicationManagement.connectedChannels[connectionAlias].registerChannelEventsCallBack(callBackId, connectionEventsCallBack)

    @staticmethod
    def UnregisterChannelEventsCallBack(connectionAlias, callBackId):
        if not CommunicationManagement.is_connected(connectionAlias):
            raise PythonComException("Channel not connected or channel alias is invalid, "
                                     "make sure to pass valid channel Alias !")

        print("unregister call back {} of connection {}".format(callBackId, str(connectionAlias)))

        CommunicationManagement.connectedChannels[connectionAlias].unregisterChannelEventsCallback(callBackId)

    @staticmethod
    def SetMode(connectionAlias, mode):
        """set mode
        """
        try:
            print("Set Mode of {} to {}".format(connectionAlias,str(mode)))

            m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)

            comm_mode = CommunicationMode.REGULAR_MODE
            if mode == CommunicationMode.CONSOLE_MODE.value:
                comm_mode = CommunicationMode.CONSOLE_MODE

            return m_commAlgo.SetMode(comm_mode)
        except Exception as e:
            print("Exception from setMode to " + connectionAlias + " to mode " + str(mode) + " " + str(e))
            raise e

    @staticmethod
    def SendTerminalString(connectionAlias, command, waitForPrompt=True):
        """send terminal string to the device. if waitForPrompt is true , wait and return the buffer

         command: command to write to the device

         waitForPrompt: True in default

        connectionAlias : connection Alias

         return: Bytes number or buffer content if waitForPrompt is True
        """

        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)

        return m_commAlgo.SendTerminalString(command, waitForPrompt)

    @staticmethod
    def GetBuffer(connectionAlias, timeOutSeconds, max_bytes=4096):
        """Read buffer

        param timeOutSeconds: timeout in seconds

        connectionAlias : connection Alias

        return: buffer content
        """
        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)

        return m_commAlgo.GetBuffer(timeOutSeconds, max_bytes=max_bytes)

    @staticmethod
    def SendCommandAndGetBufferTillPrompt(connectionAlias, command, timeOutSeconds=10):
        """Sending given command , wait until reading prompt or timeout occurs.

        command: command to be executed

        timeOutSeconds: timeout in seconds

        connectionAlias : connection Alias

        return: buffer content
        """

        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)

        return m_commAlgo.SendCommandAndGetBufferTillPrompt(command, timeOutSeconds)

    @staticmethod
    def GetBufferTillPrompt(connectionAlias, timeOutSeconds=10, shellPrompt=None):
        """read the buffer until prompt, or until timeout occurs.

        connectionAlias : connection Alias

         timeOutSeconds:  time out in second , default = 10

         return: buffer content
        """

        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)

        return m_commAlgo.GetBufferTillPrompt(timeOutSeconds, shellPrompt)

    @staticmethod
    def SetShellPrompt(connectionAlias, prompt):
        """update shell prompt

        connectionAlias : connection Alias

         prompt: prompt

         return: None
        """

        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)

        m_commAlgo.SetShellPrompt(prompt)

    @staticmethod
    def SendCommandAndGetBufferTillPromptDic(connectionAlias, command, dicPattern, timeOutSeconds=10):
        """update shell prompt

        connectionAlias : connection Alias

         prompt: prompt

         dicPattern : dictionary of regex pattern

         return: isMatched , matched Pattern , re.match object
        """

        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)
        return m_commAlgo.SendCommandAndGetBufferTillPromptDic(command, dicPattern, timeOutSeconds)

    @staticmethod
    def SetDoReconnect(connectionAlias, need_reconnect):
        """
        Alows the user to set if he wants the base layer to try reconnect when connection lost or not
        :param connectionAlias: connection Alias
        :param need_reconnect: bool parameter that indicates if we want to reconnect or not
        :return: void
        """

        m_commAlgo = CommunicationManagement.activateConnectionChannel(connectionAlias)
        return m_commAlgo.SetDoReconnect(need_reconnect)

    @staticmethod
    def GetConnectedChannels():
        """
        :return: list of connected channels (aliases)
        """
        channelsList = []
        try:
            for key in CommunicationManagement.connectedChannels:
                channelsList.append(key)
            return channelsList

        except BaseException as e:
            raise Exception("CommunicationManagment.GetConnectedChannels(): " + str(e))

    @staticmethod
    def GetSerialPortsList():
        return CommunicatioUtilities.GetSerialPortsList()

    @classmethod
    def getCommunicationAlgo(cls, prompt=None):

        # if commType == CommunicationType.CoSSerial or\
        #    commType == CommunicationType.CoSTelnet:
        #     return CoSCommunicationAlgo()
        return PyCommunicationAlgo(prompt)

    @classmethod
    def activateConnectionChannel(self, connectionAlias):
        m_commAlgo = None
        try:
            if (connectionAlias is None):
                raise Exception()
            channel = self.connectedChannels[connectionAlias]
            if channel is None:
                raise Exception()
            m_commAlgo = channel
        except Exception:
            raise PythonComException("Channel not connected or channel alias is invalid, "
                                     "make sure to pass valid channel Alias ! ")

        return m_commAlgo

    @classmethod
    def removeFromConnectionChannelDict(self, connectionAlias):
        try:
            if (connectionAlias is None):
                raise Exception()
            del self.connectedChannels[connectionAlias]

        except Exception:
            raise PythonComException("Channel alias not found !")

    @classmethod
    def addToConnectionChannelDict(cls, connectionAlias, connAlgo):
        try:
            if (connectionAlias is None):
                raise Exception()
            cls.connectedChannels[connectionAlias] = connAlgo

        except Exception:
            raise PythonComException("Channel alias not found !")

    @classmethod
    def verifyConnectivity(cls, connectionAlias):

        for alias in cls.connectedChannels:
            if alias == connectionAlias:
                raise Exception("Connection Failed : Connection Already Exists !")

        pass

    @classmethod
    def is_connected(cls, connectionAlias):
        connectedList = cls.GetConnectedChannels()
        return connectionAlias in connectedList

    @classmethod
    def createExpectedAlias(cls, commType, port, ipAddr, uname, **extraParameters):

        if extraParameters.get("uid") and extraParameters["uid"]:
            return None

        if commType.value == CommunicationType.PyTelnet.value or commType.value == CommunicationType.CoSTelnet.value:
            return str(ipAddr) + ":" + str(port)

        elif commType.value == CommunicationType.PySerial.value or commType.value == CommunicationType.CoSSerial.value:
            return "COM" + str(port)

        elif commType.value == CommunicationType.PySSH.value:
            return str(ipAddr) + ":" + uname + ":" + str(port)

        return None

    # def _private(self):  #     raise Exception("can't access this method ! ")
