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

from PyInfraCommon.BaseTest.BaseTestStructures.Types import TestDataCommon


class BaseDutInfo(TestDataCommon):
    """
    class for storing various Dut Info
    """
    def __init__(self):
        super(BaseDutInfo,self).__init__(table_title="Dut Information")
        self._Customer_Name = ""  # e.g. Cisco | H3C | CPSS_DB | CPSS_RD
        self._Project = ""  # e.g. ALDRIN | Tesla
        self.Board_Model = ""  # e.g. DB-Xcat | Sx550XG
        self.ASIC = ""  # e.g. Aldrin , Hooper
        self.Software_Version = ""
        self.UBOOT_Version = ""
        self.Linux_Version = ""
        self.CPU_CoreClock = ""
        self._CPU_CoreClock = ""
        
    @property
    def CPU_CoreClock(self):
        return self._CPU_CoreClock

    @CPU_CoreClock.setter
    def CPU_CoreClock(self,val):
        if isinstance(val,(int,float)):
            self._CPU_CoreClock = "{}MHz".format(val)
        else:
            self._CPU_CoreClock = val
