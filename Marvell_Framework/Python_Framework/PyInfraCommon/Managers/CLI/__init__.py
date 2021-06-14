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
from builtins import range
from builtins import object
from anytree import NodeMixin
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfraCommon.BaseTest.BaseTestExceptions import TestCrashedException
from PyInfraCommon.ExternalImports.Communication import PyBaseComWrapper
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from abc import abstractmethod,ABCMeta


class CliContextNode(NodeMixin):
    """
    represents a CLI Context
    :type name: str
    """
    def __init__(self, context_base_name=None,context_re_ptrn=None, args=None, parent=None):
        """
        :param context_base_name:the context base name of the Context instance e.g. : "interface" | "Config" | "enable"
        :param context_re_ptrn: the regex pattern to recognize the context
        :param args: arguemnts for context
        :param parent: reference to parent Node or None if this node is the root context Node
        """
        super(self.__class__,self).__init__()
        self.name = context_base_name
        self.pattern = context_re_ptrn
        self.cmd_name = context_base_name
        self.name = self.__class__._normalize_name(context_base_name)
        if args is not None:
            self.cmd_name += " "+ str(args)
        self.args = args
        self.parent = parent
        self.separator = "->"

    @staticmethod
    def _normalize_name(name):
        """
        :rtype: str
        :returns a normalized name
        :param name: input name
        :type name: str
        """
        ret = ""
        if name and type(name) is str:
            ret = name.lower().replace(" ","_").replace("-","_")
        return ret


class CliContextManager(object):
    """
    this class provides CLI actions such as current context type recognition
    using prompt to context dictionary
    and changing context option to change contexts using a tree data structure in order to traverse between any context
    :type _context_trees: list[CliContextNode]
    :type cli_channel: PyBaseComWrapper
    :type _currentContext: str
    :type prompts2contexts: dict[str,str]
    :type auto_detect_context: bool
    :param context_trees: list of context trees
    :param prompts2contexts: dictionary of regex prompt patterns to context type
    :param auto_detect_context: if current context is not known automatically call to _detect_context()
    """
    def __init__(self, cli_channel ,prompts2contexts, context_trees, auto_detect_context=True):
        try:
            kwargs = locals()
            newkwargs = {k:v for k,v in kwargs.items() if k != "self"}
            self._validate_init_prms(**newkwargs)
        except TestCrashedException as e:
            # TODO: validation failed should we Raise Exception?
            GlobalLogger.logger.error(str(e))
            raise
        self.auto_detect_context = auto_detect_context
        self._context_trees = context_trees
        self.channel = cli_channel
        self._currentContext = None  # current context
        self._prompt2Context = prompts2contexts
        self._support_contexts = list(self._prompt2Context.values())
        self._promptlist_re = list(prompts2contexts.keys())
        for i in range(len(self._promptlist_re)):
            prompt = self._promptlist_re[i]
            if not prompt.endswith(r"\Z") and not prompt.endswith(r"\Z)"):
                prompt += r"\Z"
            self._promptlist_re[i] = prompt

    @property
    def context(self):
        """
        :returns: current context type
        :rtype: str
        if  current Context is None try to detect if from the CLI Channel
        """
        if self._currentContext is not None:
            return self._currentContext
        else:
            if self.auto_detect_context:
                self._currentContext = self._detect_context()
            return self._currentContext

    @context.setter
    def context(self,context):
        self._currentContext = context

    def change_context(self,new_context_type,new_context_command):
        """
        change current context to new_context name
        :param new_context_type: the type of context we want to switch to e.g. "interface vlan" | "interface_vlan"
        should be in self._support_contexts
        :param new_context_command: the actual command to switch to context e.g. "interface vlan 5"
        :return: True upon success or False otherwise
        :rtype:bool
        """
        funcname = GetFunctionName(self.change_context)
        ret = True
        if not self.context:
            try:
                self._detect_context()
            except TestCrashedException as e:
                # failed to detect context
                ret = False
                err = funcname+" failed to detect current context, can't continue\n"
                GlobalLogger.logger.error(err)
                return ret
        new_context = CliContextNode._normalize_name(new_context_type)
        if new_context in self._support_contexts:
            from anytree.walker import Walker,WalkError
            # start search the context in the relevant tree
            w = Walker()
            err = None
            for context_tree in self._context_trees:
                # type: CliContextNode
                try:
                    path = w.walk(self.context,new_context)
                    ret = True
                    pass
                except WalkError as we:
                    err = funcname+ " Failed to change context using tree walker got exception: {}".format(str(we))
                except Exception as e:
                    err = funcname+ " Failed to change context got exception: {}".format(str(e))
                finally:
                    if err:
                        GlobalLogger.logger.error(err)
                        ret = False
                return ret

    @staticmethod
    def new_context(*args):
        """
        :returns a CliContext node instance that can be filled with values
        :rtype: CliContextNode
        """
        return CliContextNode(*args)

    def _detect_context(self):
        funcname = GetFunctionName(self._detect_context)
        if self.channel is not None:
            if self._promptlist_re is not None:
                # try to detect context
                ret_prompts = self.channel.SendCommandAndGetFoundPatterns(self.channel.newlineChar, self._promptlist_re, False)
                if not not ret_prompts:
                    # found something
                    if len(ret_prompts) > 1:
                        msg = funcname + " there are more than 1 found prompts that matches to input contexts\n"
                        msg += "found prompts patterns: {\n}".join(ret_prompts)
                        msg += "\nChoosing First Match"
                        GlobalLogger.logger.debug(msg)
                        for matched_prompt in ret_prompts:
                            if self._prompt2Context.get(matched_prompt,None):
                                self.context = self._prompt2Context[matched_prompt]
                    elif len(ret_prompts) == 1:
                        if self._prompt2Context.get(ret_prompts[0],None):
                            self.context = self._prompt2Context[ret_prompts[0]]
                        else:
                            err = funcname+": the found context prompt '{}' has no associated context in {} dictionary"\
                            .format(ret_prompts[0],self.__class__.__name__)
                            raise TestCrashedException(err)
                    return self.context
                else:
                    return None
            else:
                err = funcname + "can't detect context since prompt2Context dictionary is not initilized"
                raise TestCrashedException(err)
        else:
            err = funcname + "can't detect context since communication channel to Dut is not initilized"
            raise TestCrashedException(err)
            pass

    def _validate_init_prms(self,**kwargs):
        funcname = GetFunctionName(self._validate_init_prms)
        for name ,val in list(kwargs.items()):
            if name == "cli_channel":
                if val and not isinstance(val,PyBaseComWrapper):
                    err = funcname+" received {} is not a valid dut channel".format(name)
                    raise TestCrashedException(err)
            elif name == "prompts2contexts":
                if not val or type(val) is not dict:
                    err = funcname+" received {} is not a valid dictionary of prompts to contexts".format(name)
                    raise TestCrashedException(err)
            elif name == "context_trees":
                if not val or type(val) is not CliContextNode:
                    err = funcname+" received {} is not a valid Node of context trees (CliContextNode)".format(name)
                    raise TestCrashedException(err)
            else:
                return


class CliBasePrompts(object):
    """
    this class is base for any CLI based Manager that relies on context detection
    it defines common method to and some abstract methods to be implemented in its children
    :type _contextTree: CliContextNode
    :type _prompt2Context: dict[str,CliContextNode]
    """

    def __init__(self):
        """
        all self prompts should be defined in this methods childern
        e.g.
        self.cmd_shell = r"(->\s*)\Z"
        self.LUANonCLIShell = r"(lua>\s*)\Z"
        self.lua_cli_shell = r"(Console#\s*)\Z"
        self.config = r"\(config\)#\s*\Z"
        self.lua_cli_interface_eport = r"\(config-if-eport\)#\s*\Z"
        self.lua_cli_interface_ethernet = r"\(config-if\)#\s*\Z"
        self.interface_vlan = r"\(config-vlan\)#\s*\Z"
        """
        self._contextTree = None
        self._prompt2Context = None


    @abstractmethod
    def set_context_tree(self):
        """
        this method should be implemented by all children of this class
        it should create the context_tree of all cli contexts
        :return: Context tree
        :rtype: CliContextNode
        e.g.:
        cmd_shell = CliContextNode("LUANonCLIShell" , cls.cmd_shell)
        lua_cli_shell = CliContextNode("lua_cli_shell" , cls.lua_cli_shell , parent=cmd_shell)
        LUANonCLIShell = CliContextNode("LUANonCLIShell" , cls.LUANonCLIShell , parent=lua_cli_shell)
        config = CliContextNode("config" , cls.config , parent=lua_cli_shell)
        lua_cli_interface_eport = CliContextNode("lua_cli_interface_eport" , cls.lua_cli_interface_eport , parent=config)
        lua_cli_interface_ethernet = CliContextNode("lua_cli_interface_ethernet" , cls.lua_cli_interface_ethernet , parent=config)
        interface_vlan = CliContextNode("interface_vlan" , cls.interface_vlan , parent=config)
        self._contextTree = cmd_shell
        return cmd_shell
        """
        pass


    def get_context_tree(self):
        """
        Do Not Override this function in children
        :return: self context tree
        :rtype: CliContextNode
        """
        if hasattr(self,"_contextTree"):
            if self._contextTree is not None and isinstance(self._contextTree,CliContextNode):
                return self._contextTree
        return self.set_context_tree()

    def set_prompt_to_contexts(self):
        """
        create a dictionary of all  prompts to contexts and return it
        :return:dictionary of prompts to contexts
        :rtype: dict[str,str]
        """
        from enum import Enum,EnumMeta
        self._prompt2Context = {v: k for k, v in list(self.__dict__.items())
                                if v and type(v) is str and not k.startswith("__")}
        # if didnt fill _prompt2Context check if the dict is enum class
        if len(self._prompt2Context) == 0:
            self._prompt2Context = {v.value: k for k, v in list(self.__dict__.items())
                                if v and isinstance(v,Enum) and not k.startswith("__")}
        return self._prompt2Context

    def get_prompt_to_contexts(self):
        """

        :return: dictionary of prompt to context
        :rtype: dict[str,str]
        """
        if hasattr(self,"_prompt2Context"):
            if self._prompt2Context is not None:
                return  self._prompt2Context

        return self.set_prompt_to_contexts()


