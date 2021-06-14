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


import logging

class CallbackLogHandler(logging.Handler):
    def __init__(self):
        super(CallbackLogHandler, self).__init__()
        self.logFuncsLst = []

    def addLogFunc(self, logFunc):
        self.logFuncsLst.append(logFunc)

    def removeLogFunc(self, logFunc):
        if len(self.logFuncsLst) > 0:
            if self.logFuncsLst.index(logFunc) >= 0:
                self.logFuncsLst.remove(logFunc)

    def emit(self, record):
        if len(self.logFuncsLst) > 0:
            msg = self.format(record)
            for logger in self.logFuncsLst:
                logger(msg)
