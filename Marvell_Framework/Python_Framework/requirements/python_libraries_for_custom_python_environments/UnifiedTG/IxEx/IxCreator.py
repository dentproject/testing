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



class ixCreator(object):

    def create_tg(self, server_host, login):
        from UnifiedTG.IxEx.IxEx import IxEx
        tg = IxEx(server_host, login)
        return tg

    def create_port(self, pUri, pName):
        from UnifiedTG.IxEx.IxExPort import IxExPort
        port = IxExPort(pUri, pName)
        return port

    def create_stream(self, sName):
        from UnifiedTG.IxEx.IxExStream import IxExStream
        stream = IxExStream(sName)
        return stream

    def create_router(self):
        from UnifiedTG.IxEx.IxProtocolManagment import ixProtocolManagment
        r = ixProtocolManagment()
        return r

    def create_card(self,id,typeId):
        from UnifiedTG.IxEx.IxExChassis import IxExCard,IxExCard_NOVUS10,IxExCard_NOVUS100,IxExCard_K400,IxExCard_T400,\
            IxExCard_XM10_40GE12QSFP,IxExCard_STX4
        if typeId in [210]:
            return IxExCard_NOVUS100(id)
        elif typeId in [209,211,219,235,236]:
            return IxExCard_NOVUS10(id)
        elif typeId in [230]:
            return IxExCard_K400(id)
        elif typeId in [242]:
            return IxExCard_T400(id)
        elif typeId in [199]:
            return IxExCard_XM10_40GE12QSFP(id)
        elif typeId in [85]:
            return IxExCard_STX4(id)
        else:
            return IxExCard(id)

    def create_chassis(self, ip):
        from UnifiedTG.IxEx.IxExChassis import IxExChassis
        chassis = IxExChassis(ip)
        return chassis

class ixVirtualSshCreator(ixCreator):
    def create_tg(self, server_host, login,rsa_path = None):
        #PARAMICO FIX
        import paramiko
        from paramiko.py3compat import u
        s = 'xxx'
        s.encode()
        us = u(s)
        out = bytes()
        try:
            int(bytes(s).encode('hex'), 16)
        except Exception as e:
            pass
        from UnifiedTG.IxEx.IxEx import IxEx
        if rsa_path is None or rsa_path == "":
            import os
            #rsa_path = os.path.dirname(os.path.abspath(__file__)) +"\data\id_rsa"
            rsa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data','id_rsa')
        tg = IxEx(server_host, login,server_tcp_port=8022,rsaPath=rsa_path)
        return tg