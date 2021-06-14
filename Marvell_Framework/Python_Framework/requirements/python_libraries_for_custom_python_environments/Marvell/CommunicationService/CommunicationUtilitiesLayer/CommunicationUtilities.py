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
from builtins import object
import serial.tools.list_ports
import platform
if platform.system() == 'Windows':
    from ..Common.list_ports_winreg import *
# === Communication Utilities Layer ===

"""
This is an abstract layer ,
that provides usable functionality for serial/telnet , beside Communication Algo Layer's.

"""

class CommunicatioUtilities(object):

    @staticmethod
    # def GetSerialPortsList():
    #     """
    #     This function can be executed to get a list of ports
    #     :return: sorted list of available ports
    #     """
    #     ports_list = [str(port.device) for port in serial.tools.list_ports.comports()]
    #     ports_list.sort()
    #
    #     return ports_list


    def GetSerialPortsList():
        """
        This function can be executed to get a list of ports
        :return: sorted list of available ports
        """
        ports_list = []
        for port, desc, hwid in sorted(comports()):
            print("%s: %s [%s]" % (port, desc, hwid))
            ports_list.append(port)

        return ports_list