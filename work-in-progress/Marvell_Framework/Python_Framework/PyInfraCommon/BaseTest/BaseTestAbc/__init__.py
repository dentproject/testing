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
from abc import *
from future.utils import with_metaclass


class BaseTestAbc(with_metaclass(ABCMeta, object)):
    """
     abstract class for implementing Tests
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def _BasicTestInit(self):
        """
        this method is called before the test is run by _TestInit() Method
        it should initialize any Basic test resource required by test e.g. TG, Log File,
        And perform any common pre test actions:
        e.g. create log file, connect to relevant Dut, connect to TG, etc.
        :return:
        """

    @abstractmethod
    def SpecificTestInit(self):
        """
        This method is called before the test is run by _TestInit()
        It should initialize any specific test required resources and
        execute specific test init actions
        :return:
        """
        pass

    @abstractmethod
    def _TestInit(self):
        """
        this method is called before the test is run,
        it Calls _BasicTestInit() and Test SpecificTestInit() methods:
        and thus perform full test init
        :return:
        """

    @abstractmethod
    def FailTheTest(self, errmsg, test_result=None):
        """
        this method is used to declare test execution has failed
        it should log the error message, and possibly  run any test teardown procedures and cleanup test resources
        alternatively it could just change result
        :param errmsg: possibly a dictionary that describes an error message composed by error severity & error message
        string or just an error message string
        :param test_result: a reference to test result that can be altered to failed, if passed test will
        :return:
        """
        pass

    @abstractmethod
    def TestTearDown(self):
        """
        this method handles the test teardown procedure
        it clean and release any resources and perform any action required by this process
        :return:
        """

    @abstractmethod
    def _OnTestEnd(self):
        """
        this method should be called whenever a test has ended, it should run any test teardown procedures and
        cleanup test resources possibly marking the test result as Passed
        :return:
        :rtype bool
        """
        pass

    @abstractmethod
    def TestPreRunConfig (self):
        """
        This method is called by the RunTheTes() method
        it is meant to execute some initial pre-test configurations before actually running the tests
        if it is  unnecessary by derived class, that it can be just implemented as an empty function
        :return:
        """
        pass

    @abstractmethod
    def TestProcedure( self ):
        """
        the actual test body that contains all test logic
        :return: bool
        :rtype: bool
        """
        pass

    @abstractmethod
    def RunTest(self):
        """
        actual method which runs the test
        calls TestPreRunConfig() to perform pre-test configurations
        and then TestProcedure() to execute main test procedure
        :return: bool
        :rtype: bool
        """
        pass

    @abstractmethod
    def _TestSummary(self):
        """
        This method is meant to be used whenever a test has finished
        either by existing normally or by failing
        is should generate a formatted summary file that describes various test info
        :return:
        """
        pass

    @abstractmethod
    def DiscoverTestResources(self):
        """
        this method should be implemented in each baseclass type
        it should discover the Dut and Test Info and updated its Parent Baseclass
        which in turn should aquire the resouces and handle all inits
        :return:
        """
        pass
    @abstractmethod
    def _SetTestType(self):
        """
        this method will be used to set the relevant test group type (CV|MTS|SONIC|SV etc.)
        """
        pass

    class TestStepsABC(object):

        @abstractmethod
        def __init__(self):
            pass

        @abstractmethod
        def RunStep ( self , step ):
            """
            this method indicates the last step executed in the test
            it also logs the current step to the test log
            :param step:
            :type step:int
            :return:
            """
            pass

