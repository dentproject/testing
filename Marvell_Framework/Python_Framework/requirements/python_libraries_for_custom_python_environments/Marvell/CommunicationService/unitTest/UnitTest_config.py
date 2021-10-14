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


from builtins import str
from time import sleep, time
from psutil import process_iter
import subprocess
from os import path, environ
import logging
from ..CommunicationExceptions.Exceptions import PythonComException
from re import match

"""
All unit tests configurations, in order to invoke all unittests please run "pytest ." from main directory 
"""

SERIAL_COM_PORT = 10
TELNET_PORT_NUM = 12345
TELNET_IP_ADDR = b'127.0.0.1'
UNAME = None
PASSWORD = None
PORT_ID = "COM" + str(SERIAL_COM_PORT)

PORT_NUM_SSH = 22
HOST_NAME_SSH = "vvenus190"
UNAME_SSH = "pt-gen-jenk"
PASSWORD_SSH = "1qaz2wsx!"
SIMULATION_DIR = "cd /local/store/test_communication_service_SSH\n"
SIMULATION_EXECUTION = "./appDemoSim -e bobcat3_A0_pss_gm_wm.ini -tty -stdout comport -cmdshell\n"

CONSOLE_PROMPT = b"Console# "
SERIAL_INIT_PROMPT = b"->"
LUA_CLI = b"luaCLI\n"
CONFIGURE = b"configure\n"
END = b"end\n"
NEW_LINE_CHAR = b'\n'
CPSS_INIT = b"autoInitSystem\n"

# Try to get the Simulation Path from the Environment Variables
# and if not exists use hard-codded path
try:
    simulation_env_name = 'SIMULATION_PATH'
    sim_path = environ[simulation_env_name]
    simulation_path = path.dirname(sim_path)
    simulation_name = path.basename(sim_path)
except:
    simulation_path = r"C:\QuickStart"
    simulation_name = "!Reset ASIC for RDE.bat"

PROCNAME = "appDemoSim.exe"


def TerminateSimulation():
    logging.debug("Terminating the Simulation")
    for proc in process_iter():
        # check whether the process name matches
        if match(PROCNAME, proc.name()):
            logging.debug("Found Simulation and killing it")
            proc.kill()
            sleep(1)
            return True

    return False


def StartSimulation():
    logging.debug("Starting the Simulation")
    subprocess.Popen(simulation_name, cwd=simulation_path, shell=True, stdout=subprocess.PIPE)
    sleep(50)  # waiting for simulation to boot


def ResetBoardToConsolePrompt(connChannel):
    timeout = 10
    start_time = time()
    while True:
        connChannel.SendTerminalString(END, False)
        connChannel.SendTerminalString(NEW_LINE_CHAR, False)
        output = connChannel.GetBuffer(timeOutSeconds=3)
        if output.endswith(CONSOLE_PROMPT):
            break
        if (time() - start_time) >= timeout:
            raise PythonComException("cannot reset board to Console#\n" +
                                     "current buffer :" + output)
