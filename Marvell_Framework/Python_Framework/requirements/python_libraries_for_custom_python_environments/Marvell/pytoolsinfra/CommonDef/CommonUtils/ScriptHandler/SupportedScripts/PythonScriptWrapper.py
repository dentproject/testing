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
from ..ScriptWrapper import *
import subprocess

class PythonScriptWrapper(ScriptWrapper):
    _osCmd_ = "python"
    _scriptSuffix_ = ".py"

    def __init__(self, path = None, params = None):
        if os.path.isfile(path) is False or not str(path).endswith(".py"):
            raise PathException("Provided Path is NOT valid python file path! Cannot Execute Python Script")
        super(PythonScriptWrapper,self).__init__(path, params)

    def _cmdLine(self):
        params_str = ""
        if self.getScriptParams() is not None:
            for key, value in list(self.getScriptParams().items()):
                params_str += " " + str(key)+ " " + str(value)

        serilized_cmd_script = self._osCmd_+ " \"" + self.getScriptPath() + "\"" + params_str
        return serilized_cmd_script

    def ScriptExecuteSync(self):
        serilized_cmd_script = self._cmdLine()

        try:
            stdout = subprocess.check_output(serilized_cmd_script,stderr=subprocess.STDOUT).decode('utf-8')
            # stdout parsing for the client: removing path if it is exist
            path_orig = self.getScriptPath()
            path = path_orig.replace("\\", "\\\\")
            if stdout.find(path) != -1 \
                    or stdout.find(path_orig) != -1:
                stdout = stdout.strip().split('\n', 1)
                stdout = "\n".join(stdout[1:])
            return stdout
        except subprocess.CalledProcessError as e:
            # in case the script raised an inner exception
            raise ScriptInnerException("The Script in Path: " + self.getScriptPath() + "\n" +
                                       " Raised This Exception:\n" + e.output.decode('utf-8'))

    def ScriptExecuteAsync(self, timeout):
        serilized_cmd_script = self._cmdLine()
        process = subprocess.Popen(serilized_cmd_script)
        # starting new thread that terminate the new script's process after given timeout
        terminator_thread = ScriptWrapper.ScriptTerminatorThread(process.pid,timeout)
        # returning new script's process pid
        return process.pid
