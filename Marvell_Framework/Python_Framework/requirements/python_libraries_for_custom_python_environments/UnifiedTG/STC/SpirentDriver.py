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


from UnifiedTG.Unified.Utils import attrWithDefault
from trafficgenerator.tgn_utils import ApiType
from testcenter.stc_app import init_stc,StcApp


class spirentConnector(object):

    def __init__(self,_parent):
        self._app_driver = None
        self._parent = _parent

    def connect(self, login):
        if not self._app_driver:
            api = ApiType.tcl #python
            loger = self._parent._logger
            spirentDir = 'C:\Program Files (x86)\Spirent Communications\Spirent TestCenter '+login
            self._app_driver = init_stc(api, loger, spirentDir) # type :StcApp
            self._app_driver.connect(self._parent._server_host)

    @property
    def connected(self):
        return True if self._app_driver else False

    @property
    def session(self):
        return self._app_driver.project

    # @property
    # def session(self):
    #     return self._app_driver.session
    #
    # def add(self,chassis_ip):
    #     self.session.add_chassis(chassis_ip)