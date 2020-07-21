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

from UnifiedTG.Unified.Utils import Converter

class tgPortUri(object):
    def __init__(self, initdata=None):
        if initdata:
            data = initdata.split("/")
        else:
            data = [None, None, None]
        if data[0]:
            self.chassis = data[0]
        if data[1]:
            self.slot = data[1]
        isIp = Converter.stringIp2int(data[2])
        self.port = data[2] if isIp is None else str(isIp)
    def __str__(self):
        return self.chassis + '/' + self.slot + '/' + self.port
    def __repr__(self):
        return self.chassis + '/' + self.slot + '/' + self.port

    def __eq__(self, other):
        return self.chassis == other.chassis and self.slot == other.slot and self.port == other.port

class tgPortInfo(object):
    def __init__(self, initdata=None):
        if initdata:
            data = initdata.split(":")
        else:
            data = [None, None]
        self._uri = tgPortUri(data[1])
        self.name = data[0]
    def __eq__(self, other):
        if self._uri == other._uri and self.name == other.name:
            return True
        return False

    def __repr__(self):
        return self.name+':'+self.uri.__repr__()
    def __str__(self):
       return self.name+':'+self.uri.__repr__()
    @property
    def uri(self):
        return self._uri.__str__()
    @property
    def chassis(self):
        return self._uri.chassis
    @property
    def slot(self):
        return self._uri.slot
    @property
    def pid(self):
        return int(self._uri.port)

class tgPortsInfo(object):
    def __init__(self,initdata):
        self.pinfoList = [tgPortInfo]
        self.pinfoList.pop(0)
        for pdata in initdata:
            p = tgPortInfo(pdata)
            self.pinfoList.append(p)
    @property
    def uri_list(self):
        res = []
        for p in self.pinfoList:
            res.append(p.uri)
        return res
    @property
    def chassis_list(self):
        res = []
        for p in self.pinfoList:
            if not res.count(p.chassis):
                res.append(p.chassis)
        return res
    @property
    def cards_list(self):
        res = []
        for p in self.pinfoList:
            if not res.count(p.slot):
                res.append(int(p.slot))
        return res

    def chassis_ports(self,chassis):
        res = []
        for p in self.pinfoList:
            if p.chassis==chassis:
                res.append(p)
        return res

class tgInfo(object):
    def __init__(self, ):
        self.type = None
        self.server = None
        self.login = None
        self.portsList = list[tgPortInfo]

# prts = tgPortsInfo(["p1:10.5.224.86/15/1","p1:10.5.224.86/15/2"])
# xx= prts.uri_list
#
# prt = tgPortInfo("p1:10.5.224.86/15/1")
# x = prt.uri
# pass