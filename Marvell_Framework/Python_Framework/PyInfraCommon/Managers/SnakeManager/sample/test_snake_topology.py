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

from PyInfraCommon.ExternalImports.Communication import PySerialComWrapper
from PyInfra.SnakeTopology.SnakeTopology import *
from pytoolsinfra.PythonLoggerInfra.TestLogger.LoggerImpl.BaseTestLogger import BaseTestLogger

logger = BaseTestLogger("TestLogger", ".\\Results\\", "sampleLog1")


class kv(object):
    def __init__(self):
        self.value = ""


class Serial():
    def __init__(self, port, rate):
        self.com_number = kv()
        self.baudrate = kv()
        self.com_number.value = port
        self.baudrate.value = rate


def InitTest():
    comSettings = Serial(19, 115200)
    ExternalCPU = PySerialComWrapper(comSettings)
    ExternalCPU.testlogger = logger
    ExternalCPU.Connect()
    ExternalCPU.SendCommandAndWaitForPattern("luaCL ")
    ExternalCPU.SendCommandAndWaitForPattern("cpssInitSystem 29,1")
    ExternalCPU.SendCommand("\n")
    ExternalCPU.SendCommandAndWaitForPattern("lua", ExpectedPrompt="lua>")
    ExternalCPU.SendCommandAndWaitForPattern('require("common/exec/exec_genwrapper_JSON")', ExpectedPrompt="lua>")
    ExternalCPU.SendCommandAndWaitForPattern(".")


def testPairs():
    listOfPairs = []

    listOfPairs.append((CpssDutPort(0, 0), CpssDutPort(0, 8)))
    listOfPairs.append((CpssDutPort(0, 1), CpssDutPort(0, 9)))
    listOfPairs.append((CpssDutPort(0, 2), CpssDutPort(0, 10)))
    listOfPairs.append((CpssDutPort(0, 3), CpssDutPort(0, 11)))
    listOfPairs.append((CpssDutPort(0, 4), CpssDutPort(0, 12)))
    listOfPairs.append((CpssDutPort(0, 5), CpssDutPort(0, 13)))
    # listOfPairs.append((CpssDutPort(0, 6), CpssDutPort(0, 14)))
    # listOfPairs.append((CpssDutPort(0, 7), CpssDutPort(0, 15)))
    listOfPairs.append(CpssDutPort(0, 3))
    listOfPairs.append(CpssDutPort(0, 6))
    listOfPairs.append(CpssDutPort(0, 14))
    listOfPairs.append(CpssDutPort(0, 7))
    listOfPairs.append(CpssDutPort(0, 15))
    listOfPairs.append(CpssDutPort(0, 16))
    p = PortConfigManager(listOfPairs, 2, CpssDutPort(0, 0))
    #p.SortPorts()
    p.ComputePorts()
    # p.ComputePveLinks()


def testSnakeTopology():
    listOfPorts1 = []
    NumOfLanes1 = 2
    listOfPorts1.append((CpssDutPort(0, 0), CpssDutPort(0, 8)))
    listOfPorts1.append((CpssDutPort(0, 1), CpssDutPort(0, 9)))
    listOfPorts1.append((CpssDutPort(0, 2), CpssDutPort(0, 10)))
    listOfPorts1.append((CpssDutPort(0, 3), CpssDutPort(0, 11)))
    listOfPorts2 = []
    NumOfLanes2 = 1
    listOfPorts2.append((CpssDutPort(0, 4), CpssDutPort(0, 12)))
    listOfPorts2.append((CpssDutPort(0, 5), CpssDutPort(0, 13)))
    listOfPorts2.append((CpssDutPort(0, 6), CpssDutPort(0, 14)))
    listOfPorts3 = []
    NumOfLanes3 = 4
    listOfPorts3.append(CpssDutPort(0, 15))
    listOfPorts3.append(CpssDutPort(0, 16))
    listOfPorts3.append(CpssDutPort(0, 17))
    listOfPorts3.append(CpssDutPort(0, 18))
    listOfPorts3.append(CpssDutPort(0, 19))
    listOfPorts3.append(CpssDutPort(0, 20))
    listOfPorts3.append(CpssDutPort(0, 21))
    listOfPorts3.append(CpssDutPort(0, 22))

    st = SnakeTopology(CpssTrafficInitiator.TG_2, CpssDutPort(0, 9), CpssDutPort(0, 23))
    st.AddPortList(listOfPorts2, NumOfLanes2)
    st.AddPortList(listOfPorts1, NumOfLanes1)
    st.AddPortList(listOfPorts3, NumOfLanes3)
    #print st.PortBlocks[0].DeployPorts()
    b_list = [item for b in st.PortBlocks for item in b.Ports]
    print b_list
    print st.SetSrcDstLinks()


def testSnakeTopology2():
    listOfPorts1 = []
    NumOfLanes1 = 1
    listOfPorts1.append((CpssDutPort(0, 56), CpssDutPort(0, 64)))
    listOfPorts1.append((CpssDutPort(0, 57), CpssDutPort(0, 65)))
    listOfPorts1.append((CpssDutPort(0, 58), CpssDutPort(0, 66)))
    listOfPorts1.append((CpssDutPort(0, 59), CpssDutPort(0, 67)))
    listOfPorts1.append((CpssDutPort(0, 68), CpssDutPort(0, 69)))
    listOfPorts1.append((CpssDutPort(0, 71), CpssDutPort(0, 70)))

    st = SnakeTopology(CpssTrafficInitiator.CPU, CpssDutPort(0, 56))
    st.AddPortList(listOfPorts1, NumOfLanes1)
    #print st.PortBlocks[0].DeployPorts()
    b_list = [item for b in st.PortBlocks for item in b.Ports]
    print b_list
    print st.SetSrcDstLinks()
    pass

def testSnakeTopology3():
    listOfPorts1 = []
    NumOfLanes1 = 1
    # listOfPorts1.append(CpssDutPort(0, 56))
    # listOfPorts1.append(CpssDutPort(0, 64))
    # listOfPorts1.append(CpssDutPort(0, 57))
    # listOfPorts1.append(CpssDutPort(0, 65))
    # listOfPorts1.append(CpssDutPort(0, 58))
    # listOfPorts1.append(CpssDutPort(0, 66))
    # listOfPorts1.append(CpssDutPort(0, 59))
    # listOfPorts1.append(CpssDutPort(0, 67))
    # listOfPorts1.append(CpssDutPort(0, 68))
    # listOfPorts1.append(CpssDutPort(0, 69))
    # Case 1
    # listOfPorts1.append((CpssDutPort(0, 1), CpssDutPort(0, 2)))
    # listOfPorts1.append(CpssDutPort(0, 3))
    # listOfPorts1.append((CpssDutPort(0, 4), CpssDutPort(0, 5)))
    # listOfPorts1.append(CpssDutPort(0, 6))
    # Case 2
    #listOfPorts1.append(CpssDutPort(0, 1))
    #listOfPorts1.append(CpssDutPort(0, 2))
    listOfPorts1.append((CpssDutPort(0, 1), CpssDutPort(0, 2)))
    listOfPorts1.append(CpssDutPort(0, 3))
    listOfPorts1.append(CpssDutPort(0, 4))
    listOfPorts1.append(CpssDutPort(0, 5))
    listOfPorts1.append(CpssDutPort(0, 6))
    # listOfPorts1.append((CpssDutPort(0, 59), CpssDutPort(0, 67)))
    # listOfPorts1.append((CpssDutPort(0, 68), CpssDutPort(0, 69)))
    # listOfPorts1.append(CpssDutPort(0, 71))
    # listOfPorts1.append(CpssDutPort(0, 70))

    st = SnakeTopology(CpssTrafficInitiator.CPU, CpssDutPort(0, 56))
    st.AddPortList(listOfPorts1, NumOfLanes1)
    #print st.PortBlocks[0].DeployPorts()
    b_list = [item for b in st.PortBlocks for item in b.Ports]
    print b_list
    print st.SetSrcDstLinks()
    pass

if __name__ == "__main__":
    testSnakeTopology3()
    pass