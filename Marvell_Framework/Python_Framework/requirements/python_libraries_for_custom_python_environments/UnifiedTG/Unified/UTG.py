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

import sys
import logging
from collections import OrderedDict

from UnifiedTG.Unified.ObjectCreator import objectCreator
from UnifiedTG.Unified.UtgObject import UtgObject

from UnifiedTG.Unified.TG import TG
from UnifiedTG.Unified.Port import Port

from pycore.logger_utils.ReportFormatter import ReporterFormatter


class utg(object):
    tgs = OrderedDict() #type: list[TG]
    ports = OrderedDict()  #type: list[Port]
    def _addport(cls,name,port):
        cls.ports[name] = port

    @classmethod
    def connect(cls, tg_type, server_host, login_name, logger=None,rsa_path = None):
        """ Create TG.

        :rtype: TG
        :param tg_type: TG type
        :param server_host: TG server IP (e.g. IxTclServer IP)
        :param logger: python logger, if None default logger writing to stdout and log file in temp directory will be created.
        """

        if not logger:
            logger = logging.getLogger('utg')
            logging.raiseExceptions = False
            logger.setLevel(logging.DEBUG)
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(ReporterFormatter('[%(asctime)s] %(message)s'))
            logger.addHandler(sh)
            if sys.platform.startswith('win'):
                fh = logging.FileHandler(r"c:\temp\utg_log.txt", 'w')
            else:
                fh = logging.FileHandler(r"/tmp/utg_log.txt", 'w')
            fh.setFormatter(ReporterFormatter('[%(asctime)s] %(message)s'))
            logger.addHandler(fh)

        UtgObject._logger = logger
        creator = objectCreator(tg_type)
        cls.tgs[server_host] = creator.create_tg(server_host, login_name,rsa_path=rsa_path)
        return cls.tgs[server_host]
