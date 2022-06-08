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
import pytest, logging, sys
from ..ScriptHandlerAPI import *

logger = logging.getLogger()
logger.level = logging.DEBUG # DEBUG / INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

current_dir = os.path.dirname(__file__) + '\\scriptsForTesting\\'

def testNoneAsPath():
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest None path to script Executer\n")
    script_path = None
    try:
        output = ScriptHandlerAPI.ExecuterSync(script_path)
        assert False # when test gets here failed to handle NONE as path
    except PathException as e:
        assert str(e) != ""
        logging.debug("The exception should indicate Path is None:\n"+str(e))

def testUnsupportedScriptSuffix():
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest unsupported suffix of script\n")
    try:
        script_path = r"C:\unsupportedScript.suffix"
        output = ScriptHandlerAPI.ExecuterSync(script_path)
        assert False # when test gets here failed to handle unsupported suffix
    except WrongTypesException as e:
        assert str(e) != ""
        logging.debug("\nThe Exception should indicate unsupported suffix:\n" + str(e))

def testNOTExistPath():
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest handling with NOT exists path\n")
    script_path = r"C:\NOT_Exist.py"
    try:
        output = ScriptHandlerAPI.ExecuterSync(script_path)
        assert False # when test gets here failed to handle NOT exists path
    except PathException as e:
        assert str(e) != ""
        logging.debug("\nThe exception should indicate Path is invalid:\n"+str(e))

outputScripts = {"Python": current_dir + 'pythonOutputScript.py'
                }
@pytest.mark.parametrize(("current_script"), (outputScripts))
def testExecuteSyncScriptsWithOutput(current_script):
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nExecute The script with output of " + current_script+"\n")
    script_path = outputScripts[current_script]
    script_params = {"first": 1, "second": 2}

    stdout = ScriptHandlerAPI.ExecuterSync(script_path, script_params)

    expected_output = "Execute " +str(current_script)+ " script Successfully"
    assert expected_output == stdout

nonOutputScripts = {"Python": current_dir + 'pythonNoOutputScript.py'
                }
@pytest.mark.parametrize(("current_script"), (nonOutputScripts))
def testExecuteSyncScriptsWithNoOutput(current_script):
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nExecute The script with no output of " + current_script)

    script_path = nonOutputScripts[current_script]
    stdout = ScriptHandlerAPI.ExecuterSync(script_path)

    expected_output = ""
    assert expected_output == stdout

exceptionScripts = {"Python": current_dir + 'pythonExceptionScript.py'
                }
@pytest.mark.parametrize(("current_script"), (exceptionScripts))
def testCatchingExceptionFromScript(current_script):
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest catching script inner exception\n")
    script_path = exceptionScripts[current_script]

    try:
        output = ScriptHandlerAPI.ExecuterSync(script_path)
        assert False # when test gets here test didn't catch inner script exception
    except ScriptInnerException as e:
        assert str(e) != ""
        logging.debug("\nThe script inner exception is:\n" + str(e))

def testTerminateInvalidPID():
    invalid_pid = -1
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest Terminate Invalid Process ID")
    try:
        ScriptHandlerAPI.TerminateSync(invalid_pid)
        assert False  # when test gets here termination of process has been failed
    except ProcessIDException as e:
        assert str(e) != ""
        logging.debug("\nThe exception should indicate PID is invalid:\n"+str(e))

infiniteScripts = {"Python": current_dir + 'pythonInfiniteScript.py'
                  }

pids = {}

@pytest.mark.parametrize(("current_script"), (infiniteScripts))
def testExecuteAsyncWithoutTimeout(current_script):
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest Execute Asynchronous script WITHOUT timeout")

    script_path = infiniteScripts[current_script]
    script_params = {"first": 1, "second": 2}
    current_pid = ScriptHandlerAPI.ExecuterAsync(script_path, script_params)

    pids[current_script] = current_pid
    logging.debug("\nProcess of " + current_script + "has PID: " + str(current_pid))


@pytest.mark.parametrize(("current_script"), (infiniteScripts))
def testTerminate(current_script):
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest Terminate Process")

    current_pid = pids.pop(current_script)
    ScriptHandlerAPI.TerminateSync(current_pid)
    logging.debug("\nProcess with pid: " + str(current_pid) + " was terminated")
    try:
        time.sleep(1)
        ScriptHandlerAPI.TerminateSync(current_pid)
        assert False  # when test gets here termination of process has been failed
    except ProcessIDException as e:
        assert str(e) != ""
        logging.debug("\nThe exception should indicate PID is invalid:\n"+str(e))

@pytest.mark.parametrize(("current_script"), (infiniteScripts))
def testExecuteAsyncWithTimeout_5sec(current_script):
    logging.debug("\n\n===============================================================\n\n")
    logging.debug("\nTest Execute Async with timeout of 5 sec")

    script_path = infiniteScripts[current_script]
    script_params = {"first": 1, "second": 2}
    timeout = 5
    current_pid = ScriptHandlerAPI.ExecuterAsync(script_path, script_params,timeout)
    try:
        time.sleep(7)
        logging.debug("\nThe process with PID: " + str(current_pid) + " has been terminated")
        ScriptHandlerAPI.TerminateSync(current_pid)
        assert False  # when test gets here termination of process has been failed
    except ProcessIDException as e:
        assert str(e) != ""
        logging.debug("\nThe exception should indicate PID is invalid:\n"+str(e))
