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

from threading import Lock
from PyInfraCommon.ExternalImports.TG import TG


class TGConnectionsManager:
    __lock = Lock()
    __tg_connections = {}

    @classmethod
    def __GetUri(self, server_host, login_name, ports):
        """
        :param server_host:
        :type server_host:
        :param login_name:
        :type login_name:
        :param ports:
        :type ports:
        :return: unique uri key based on input
        :rtype:
        """
        return "{}-{}-{}".format(server_host, login_name, ports)

    @classmethod
    def GetInstance(cls,server_host, login_name, ports):
        """
        get tg instance from internal dict base on input args
        :param server_host: ip of chassis used for connection
        :type server_host: str
        :param login_name: login name used by Ixia
        :type login_name: str
        :param ports: list of ports in uri format as required by connecting to TG
        :type ports: list
        :return:TG instance or None of none existsing
        :rtype:TG
        """
        tg = None
        try:
            cls.__lock.acquire()
            tg = cls.__tg_connections.get(cls.__GetUri(server_host,login_name,ports),None)
        finally:
            cls.__lock.release()
            return tg

    @classmethod
    def Register_Instance(cls,server_host, login_name, ports,utg_instance):
        """
        registers utg_instance in this container
        :param server_host:
        :type server_host:
        :param login_name:
        :type login_name:
        :param ports:
        :type ports:
        :param utg_instance:
        :type utg_instance:
        :return:
        :rtype:
        """
        try:
            uri = cls.__GetUri(server_host, login_name, ports)
            cls.__lock.acquire()
            cls.__tg_connections[uri] = utg_instance
        finally:
            cls.__lock.release()

