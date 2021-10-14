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
from builtins import object
from Marvell.pytoolsinfra.CommonDef.CommonUtils.Switch import Switch, case
from Marvell.CommunicationService.CommunicationExceptions.Exceptions import PythonComException
from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl.PyComWrapper import PyBaseComWrapper
from Marvell.CommunicationService.CommunicationWrapper.ComWrapperImpl import PySerialComWrapper, PyTelnetComWrapper, \
    PySSHComWrapper
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.Core.ABCConfigurationReader import ABCConfigurationReader

from Marvell.ResourceManagement import *
from Marvell.pytoolsinfra.ConfigurationModule.Configurator.ConfigurationManager.ConfigManager import ConfigManager
import platform


class ResourceManager(object):
    _setupNum = 1
    _config_data = GetConfigData()

    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate static class')

    @classmethod
    @LogWith(ResourceManager_logger, show_func_parameters)
    def SetSetupNum(cls, setup_num):
        # type: (int) -> None
        """
        This function allows the user to set the "Setup Number" he wants the Resource manager will use
        :param setup_num: int 1 -> ...
        :return:None
        """
        cls._setupNum = setup_num

    @classmethod
    @LogWith(ResourceManager_logger, show_func_parameters)
    def GetChannel(cls, channelName, connect=False, current_config_file="", sheet_name=None,section_name=None):
        # type: (str, bool) -> PyBaseComWrapper
        """
        This function gets a string that represent some entry in the connection section (e.g. "Com External CPU")
        and in the table we will have the real type that this channel is related to
        for example:
            in the connection data section we will have:
            "Com External CPU" = "serial1"

            and at the section "serial1" we will have:
            connection type = serial
            com port = 4
        :param connect:
        :param channelName: string that represent some entry in the connection section
        :paramsheet_key: string that allows to ovveride excel default sheet key
        :return: object of type "PyBaseComWrapper"
        """
        low_strip = ABCConfigurationReader.low_strip
        channelName = low_strip(channelName)

        # channelName = channelName.lower().replace(" ", "_")
        # the attribute name we use to identify the type of Channel
        type_attr_name = "_proto_type"
        connection_data = cls.GetConnectionData(channelName, type_attr_name, current_config_file=current_config_file, sheet_name=sheet_name,
                                                section_name=section_name)
        result = None
        the_type = "default"
        if hasattr(connection_data,type_attr_name):
            the_type = getattr(connection_data, type_attr_name)
            if isinstance(the_type, bytes):
                the_type = the_type.decode('utf-8')

            while Switch(the_type):
                if case("serial"):
                    result = PySerialComWrapper.PySerialComWrapper(connection_data)
                    break
                if case("telnet"):
                    result = PyTelnetComWrapper.PyTelnetComWrapper(connection_data)
                    break
                if case("ssh"):
                    result = PySSHComWrapper.PySSHComWrapper(connection_data)
                    break
                if case("default"):
                    err = "ResourceManager.GetChannel Failed!!\n"
                    err += "Did not recognize the type of {} channel ".format(channelName)
                    raise PythonComException(err)

        if result is not None:
            if connect:
                result.Connect()
        else:
            err = "'ComWrapperImpl.ResourceManager.GetChannel' Failed!!\n" + "You must reconnect "
            raise PythonComException(err)
        return result

    @classmethod
    @LogWith(ResourceManager_logger, show_func_parameters)
    def GetConnectionData(cls, channelName, type_attr_name=None, current_config_file="", sheet_name=None, section_name=None):
        if current_config_file == "":
            current_config_file = cls.GetSetupPath()

        if isinstance(current_config_file, bytes):
            current_config_file = current_config_file.decode('utf-8')

        if current_config_file.startswith('.'):
            import os
            current_config_file = current_config_file.replace('.',os.path.dirname(os.path.realpath(__file__)))

        current_key = cls._config_data.setup_reasource_data.communication_section_name if sheet_name is None else "{}.{}".format(sheet_name, section_name)

        manager = ConfigManager()
        commSettings = manager.get_obj(current_key, current_config_file, section_type_key=type_attr_name)

        try:
            sectionName = getattr(commSettings, channelName)
        except Exception as e:
            raise PythonComException("The channel name doesnt exists")

        connectionDetails = cls.GetConnectionDetails(sectionName.value, type_attr_name, current_config_file=current_config_file,sheet_name=sheet_name)
        return connectionDetails

    @classmethod
    @LogWith(ResourceManager_logger, show_func_parameters)
    def GetConnectionDetails(cls, sectionName,type_attr_name=None, current_config_file="",sheet_name=None):
        # type: (str) -> object
        """
        to do : get the section from the Configuration manager
        :param sectionName:
        :param type_attr_name: the attribute name we use to identify the type of Channel
        :return: Object that represent some connection data
        """

        if isinstance(sectionName, bytes):
            sectionName = sectionName.decode('utf-8')

        if current_config_file == "":
            current_config_file = cls.GetSetupPath()
        current_key = cls._config_data.setup_reasource_data.base_entry_name + sectionName.lower() if sheet_name is None else "{}.{}".format(sheet_name,sectionName.lower())
        manager = ConfigManager()
        tmp = manager.get_obj(current_key, current_config_file, section_type_key=type_attr_name)
        return tmp

    @classmethod
    @LogWith(ResourceManager_logger, show_func_parameters)
    def GetSetupPath(cls, setup_name="", setup_list_path="", settings_section_name="", attribute_name=""):
        manager = ConfigManager()
        low_strip = ABCConfigurationReader.low_strip

        if setup_list_path == "":
            setup_list_path = cls._config_data.setup_reasource_data.setup_list_path

        setup_list_path = cls.FixPathForOS(setup_list_path)

        if setup_list_path.startswith('.'):
            setup_list_path = os.path.dirname(os.path.realpath(__file__)) + setup_list_path[1:]

        if attribute_name == "":
            attribute_name = cls._config_data.setup_reasource_data.base_setup_attr_name + " " + str(cls._setupNum)

        attribute_name = low_strip(attribute_name)

        if settings_section_name == "":
            settings_section_name = cls._config_data.setup_reasource_data.common_settings_section_name

        if setup_name == "":
            orig_pc_name = platform.node()
            _pc_name = orig_pc_name
            try:
                setup_name = _pc_name
            except Exception as e:
                setup_name = ""

        setup_name = low_strip(setup_name.lower())

        section_obj = manager.get_obj(settings_section_name, setup_list_path)

        _pc_data = None
        try:
            if setup_name != "":
                _pc_data = getattr(section_obj, setup_name)
        except Exception as e:
            _pc_data = None

        if _pc_data is None:
            try:
                _pc_data = getattr(section_obj, "local_host")
            except Exception as e:
                raise PythonComException("Current computer name \"{}\" doesnt exists".format(setup_name))


        try:
            setup_config_file_path = getattr(_pc_data, attribute_name)
        except Exception as e:
            raise PythonComException("Setup name \"{}\" doesnt exists".format(attribute_name))

        if isinstance(setup_config_file_path, bytes):
            setup_config_file_path = setup_config_file_path.decode('utf-8')

        if setup_config_file_path.startswith('.'):
            setup_config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  setup_config_file_path[2:])

        return setup_config_file_path

    @classmethod
    def FixPathForOS(cls, setup_list_path):
        tmp_path = setup_list_path
        if platform.system() == "Linux":
            tmp_path = tmp_path.replace(r"\\fileril103\TESTING", r"\swdev\testing")
            tmp_path = tmp_path.replace(r"\\fileril103\dev", r"\swdev\fileril103")
            tmp_path = tmp_path.replace('\\', "/")

        return tmp_path

# ResourceManager = Log_all_class_methods(ResourceManager, ResourceManager_logger, show_func_parameters)

# import inspect
# def decorate_class(cls):
#     for name, method in inspect.getmembers(cls, inspect.ismethod):
#         if name != '__init__':
#             setattr(cls, name, classmethod((LogWith(str(cls.__name__),
#                                                    ResourceManager_logger, show_func_parameters)(method))))
#     return cls
#
# ResourceManager = decorate_class(ResourceManager1)
