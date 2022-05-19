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
import copy
from prettytable import PrettyTable, prettytable
from collections import OrderedDict
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName


class TestDataCommon(object):
    """
    holds common methods to manage test data
    """
    def __init__(self,table_title=None):
        self._pretty_table = None  # type: PrettyTable
        self._pretty_table_title = table_title
        self._odict = OrderedDict()
    
    def __setattr__(self, key, value):
        super(TestDataCommon, self).__setattr__(key, value)
        if not key.startswith("__") and not key.endswith("__") and not key.startswith("_") and "_odict" not in key and value is not None:
            self._odict[key] = value
            
    def is_pretty_table_generated(self):
        """
        :return: TRUE if self pretty table object was already generated
        """
        return self._pretty_table and self._pretty_table._rows
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        return not self == other
    
    def Gen_Pretty_Table(self):
        self._pretty_table = PrettyTable()
        col = []
        row = []
        for k,v in self._odict.items():
            if not v:
                v = ""
            if "_" in k:
                k.replace("_"," ")
            col.append(k)
            row.append(v)
        self._pretty_table.field_names = col
        self._pretty_table.hrules = prettytable.ALL
        self._pretty_table.align = "l"
        self._pretty_table.add_row(row)
        if self._pretty_table_title:
            self._pretty_table.title = self._pretty_table_title
        #self._pretty_table.max_width = 20
        
    def __str__(self):
        ret = ""
        if not self.is_pretty_table_generated():
            self.Gen_Pretty_Table()
        ret = self._pretty_table.get_string()
        return ret
    
    def To_HTML_Table(self):
        """
        generate self attributes representation in HTML Table format
        :return: HTML string of a table of self attributes
        :rtype: str
        """
        ret = ""
        if not self.is_pretty_table_generated():
            self.Gen_Pretty_Table()
        ret = self._pretty_table.get_html_string(format=True)
        return ret
    
    # def Concenate_Pretty_Table(self, ptable_class):
    #     funcname = GetFunctionName(self.Concenate_Pretty_Table)
    #     ptable_ref = None # type: PrettyTable
    #     if isinstance(ptable_class,PrettyTable):
    #         ptable_ref = copy.deepcopy(ptable_class)
    #     elif isinstance(ptable_class,TestDataCommon):
    #         ptable_ref = copy.deepcopy(ptable_class._pretty_table)
    #     my_rows = self._pretty_table._rows
    #     my_cols = self._pretty_table.field_names
    #     my_cols_len = len(my_cols)
    #     my_rows_len = len(my_rows)
    #     other_rows = ptable_ref._rows
    #     other_cols = ptable_ref.field_names
    #     other_rows_len = len(other_rows)
    #     other_cols_len = len(other_cols)
    #     # balance cols on each row
    #     if my_cols_len != other_cols_len:
    #         if my_cols_len > other_cols_len:
    #             for row in other_rows:
    #                 for i in range(my_cols_len - other_cols_len):
    #                     row.append("")
    #
    #     # joined_cols = self._pretty_table.field_names + other_cols
    #     # joined_rows = self._pretty_table._rows + other_rows
    #
    #
    #
    #
    #
    #
    #     # elif hasattr(ptable_class,"_pretty_table"):
    #     #     ptable_ref = copy.deepcopy(getattr(ptable_class,"_pretty_table"))
    #     # else:
    #     #     err = funcname+ " input ptable_class parameter must have a PrettyTable attribute"
    #     #     raise TypeError(err)
    #     # if not self.is_pretty_table_generated():
    #     #     self.Gen_Pretty_Table()
    #     # # concatenate field names
    #     # my_fields = self._pretty_table.field_names
    #     # other_fields = ptable_class.field_names
    #     # joined_fields = my_fields + other_fields
    #     # self._pretty_table.add_column()
        
        
        
    @property
    def table_title(self):
        return self._pretty_table_title
    
    @table_title.setter
    def table_title(self,title):
        self._pretty_table_title = title
        if self._pretty_table:
            self._pretty_table.title = title
