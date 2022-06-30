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

import os
from os.path import exists

from PyPacket.pcalyzer.shark import TSHARK_ENUMS


def detect_shark_path(app_name):
    """
    Check if wireshark available on the system and return path/None
    """
    known_path_list = ['C:\\Program Files\\Wireshark\\', 'C:\\Program Files (x86)\\Wireshark\\', '/usr/bin/wireshark',
                       '/usr/bin/tshark']

    for p in known_path_list:
        if exists(p):
            # print("return p + app_name: {} + {}".format(p, app_name))
            return p + app_name

    sys_path_list = os.environ["PATH"].split(';')
    for p in sys_path_list:
        if exists(p+app_name):
            # print("return p + app_name: {} + {}".format(p, app_name))
            return app_name
    print("known_path_list: {}".format(known_path_list))
    print("sys_path_list: {}".format(sys_path_list))
    return None

class sharkCommandBuilder(object):
    _app_name = None
    _app_path = None

    @classmethod
    def set_app_path(cls,path):
        cls._app_path = path

    def __init__(self,app_name):
        if not self.__class__._app_name:
            self.__class__._app_name = app_name
        if not self.__class__._app_path:
            self.__class__._app_path = detect_shark_path(app_name)
        self._command = []

    def build_command(self):
        if not self._app_path: #todo exception no app path
            return None
        self._command.insert(0,  self.__class__._app_path)
        return self._command

    def _append_2cmd(self,option):
        self._command.append(option)

    def add_option(self,option,value = None):
        # type: (TSHARK_ENUMS.options, str) -> None
        if option:
            self._append_2cmd(option.value)
        if value:
            self._append_2cmd(value)