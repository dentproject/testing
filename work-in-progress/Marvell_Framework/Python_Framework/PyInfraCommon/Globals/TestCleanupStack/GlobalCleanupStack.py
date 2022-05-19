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

from PyInfraCommon.GlobalFunctions.Utils.Function import function_call_params, GetFunctionName


class _GlobalCleanupStack:
    def __init__(self):
        self.__stack = []

    def Stack_Setter(self, stack:list):
        self.__stack = stack

    def Add_Cleanup_Function_To_Stack(self, func, *args, **kwargs):
        """
        adds functions to stack of functions to call to on cleanup stage
        on TestTearDown()
        :param func:  function to call to
        :param args: optional args to use when calling function
        :param kwargs: optional kwargs to use when calling function
        :return:None
        """
        funcname = GetFunctionName(self.Add_Cleanup_Function_To_Stack)
        func_params = function_call_params()
        func_params.valditate_params(funcname, func, args, kwargs)
        func_params.func = func
        if args:
            func_params.args = args
        if kwargs:
            func_params.kwargs = kwargs

        this_func_name = GetFunctionName(func_params.func)
        if 'reboot' in this_func_name.lower() in this_func_name:
            # if reboot was requested clear the stack and only push this function
            self._cleanup_stack = []
        # push to stack
        self.__stack.append(func_params)


GlobalCleanupStack = _GlobalCleanupStack()
