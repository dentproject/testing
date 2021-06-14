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

from builtins import object
from threading import Thread
from abc import abstractmethod
from ..CommunicationExceptions.Exceptions import ReadFailedException


class CommEventsCallback(object):
    @abstractmethod
    def onRead(self, data):
        pass

    @abstractmethod
    def onError(self, data):
        pass


class ChannelReader(object):
    """
    it's a derived class , that inherits and implements [[ABCCommunication.py]]
    """

    def __init__(self, m_channel):
        self._m_channel = m_channel
        self._channelEventsCallBacks = dict()
        self._is_read_polling = False
        self._read_thread = None

    def registerChannelEventsCallBack(self, callBackId, channelEventsCallBack):
        self._channelEventsCallBacks[callBackId] = channelEventsCallBack

    def unregisterChannelEventsCallback(self, callBackId):
        del self._channelEventsCallBacks[callBackId]

    def unregisterChannelEventsAllCallback(self):
        self._channelEventsCallBacks = dict()

    def startReadPolling(self):
        if self._read_thread:
            self.stopReadPolling()

        self._read_thread = Thread(target=self._readLoopThread)
        self._read_thread.start()

    def stopReadPolling(self):
        self._is_read_polling = False
        if self._read_thread:
            self._read_thread.join()
            self._read_thread = None

    def read(self, prompt=None, timeout=None, max_bytes=4096):
        try:
            data = self._m_channel.Read(prompt=prompt, timeout=timeout, max_bytes=max_bytes)
            if data and len(data) > 0:
                for callBack in list(self._channelEventsCallBacks.values()):
                    callBack.onRead(data)
            return data
        except ReadFailedException as err:
            for callBack in list(self._channelEventsCallBacks.values()):
                callBack.onError(err.message)
            raise err

    def _readLoopThread(self):
        self._is_read_polling = True
        try:
            while self._is_read_polling:
                self.read(timeout=0)
        except ReadFailedException as err:
            self._is_read_polling = False
            self._read_thread = None
