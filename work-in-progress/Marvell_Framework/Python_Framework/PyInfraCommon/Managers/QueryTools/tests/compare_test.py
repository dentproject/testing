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

from __future__ import print_function
from builtins import object
from PyInfraCommon.Managers.QueryTools.Comparator import *

class TestClassA(object):
    def __init__(self, a_val, b_val, c_val):
        self.a = a_val
        self.b = b_val
        self.c = c_val

class TestClassB(object):
    def __init__(self, a_val, b_val, c_val, d_val):
        self.tc_a = TestClassA(a_val, b_val, c_val)
        self.d = d_val


def testComparator():
    #command = TestClassB(0, 15, "HelloKitty", CompareMethod.Equal)
    command = TestClassB(0, 15, 22, 44)
    c = Comparator(command)
    #command.tc_a.c
    #c.AddCommonToCompareList('tc_a.c', 5)
    #c.AddCommonToCompareList1(command.tc_a.b, 5)
    #c.AddCommonToCompareList1(command, 5)
    #c.AddToCompareList1(command.tc_a.b, 5, CompareMethod.Diff)
    expected = 5
    c.Diff(command.tc_a.b, expected, CompareDiffOptions.AbsDiff, percent_deviation_plus=10)
    #c.Equal(command.tc_a.b, expected)
    #c.Equal(command.tc_a.c, expected)
    c.Compare()
    #c.PrintReport()

if __name__ == "__main__":
    try:
        testComparator()
    except ComparatorArgumentError as e:
        print("Message: {}, Initiator: {}".format(str(e), e.initiator))

# CpssReturnCodeEnum