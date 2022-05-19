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



class xenaCreator(object):
    def create_tg(self, server_host, login):
        from UnifiedTG.Xena.XenaTg import xenaTg
        tg = xenaTg(server_host,login)
        return tg

    def create_port(self,pUri, pName):
        from UnifiedTG.Xena.XenaPort import xenaPort
        port  = xenaPort(pUri, pName)
        return port

    def create_stream(self,sName):
        from UnifiedTG.Xena.XenaStream import xenaStream
        stream = xenaStream(sName)
        return stream

    def create_chassis(self, ip):
        from UnifiedTG.Xena.XenaChassis import xenaChasis
        return xenaChasis() #TODO