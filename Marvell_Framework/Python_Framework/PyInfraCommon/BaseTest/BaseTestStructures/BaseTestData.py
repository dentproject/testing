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

from __future__ import absolute_import
from builtins import object
from PyInfraCommon.BaseTest.BaseTestStructures.BasetTestResources import *
from PyInfraCommon.BaseTest.BaseTestStructures.BaseTestInfo import *
from PyInfraCommon.BaseTest.BaseTestStructures.BaseDutInfo import *
from .Types import TestDataCommon


class BaseTestData(object):
    """
    aggregator class that holds all test data and metadata
    -Test Information
    -Dut Information
    -Test Resources

    :type DutInfo: BaseDutInfo
    :type TestInfo: BaseTestInfo
    :type Resources: BaseTestResources
    """
    
    def __init__(self):
        self.DutInfo = BaseDutInfo()
        self.TestInfo = BaseTestInfo()
        self.Resources = BaseTestResources()
