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

from builtins import object
class TGMappingTableEntry(object):
    def __init__(self):
        self.id = ""
        self.tg_ip = ""
        self.tg_type = ""
        self.tg_card = ""
        self.resource_group = ""
        self.tg_port = ""


class TGMappingTable(object):
    def __init__(self):
        self.entries = [TGMappingTableEntry]
        self.entries.pop()

    def __getitem__(self, item):
        return self.entries[item]

    def __iter__(self):
        for entry in self.entries:
            yield entry


class TGMapping(object):
    def __init__(self):
        self.tg_mapping_table = TGMappingTable()