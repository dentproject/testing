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

from __future__ import division
from builtins import str
from past.utils import old_div
from builtins import object
from collections import OrderedDict

from PyInfraCommon.Managers.QueryTools.errorHandlers import ComparatorError, ComparatorArgumentError, ComparatorEnvironmentError
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from abc import ABCMeta, abstractmethod
from enum import IntEnum
import operator
import inspect
import re
from prettytable import PrettyTable
import os, sys
from future.utils import with_metaclass

class CompareVariableType(IntEnum):
    Unknown = 0
    Numerical = 1
    Enumerator = 3
    Boolean = 4
    Alphabetical = 5

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))


class ReportStatus(IntEnum):
    Unknown = 0
    NotComputed = 1
    AsExpected = 2
    Unexpected = 3

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name


class ResultStatusOption(IntEnum):
    Unknown = 0
    NotComputed = 1
    Equal = 2
    NotEqual = 3
    GreaterThan = 4
    LessThan = 5
    InRange = 6
    OutOfRange = 7

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name


class CompareMethod(IntEnum):
    Unknown = 0
    Equal = 1
    NotEqual = 2
    GreaterThan = 3
    LessThan = 4
    GreaterOrEqual = 5
    LessOrEqual = 6
    Bitmap = 7
    Diff = 8

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name


class CompareDiffOptions(IntEnum):
    Unknown = 0
    AbsDiff = 1
    DoubleDiff = 2

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name


class NumericCompareMode(IntEnum):
    Unknown = 0
    Numbers = 1
    Percents = 2

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))


class PrintSeverity(IntEnum):
    Low = 0
    Medium = 1
    High = 2

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name

class PrintMode(IntEnum):
    Always = 0
    OnlyOnFail = 1
    Never = 2

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

    @classmethod
    def ToString(cls, int_val):
        if not cls.HasMember(int_val):
            int_val = 0
        return cls(int_val).name

class CompareResults(object):
    def __init__(self):
        self.ExpectedValue = None
        self.ActualValue = None
        self.AcceptableDeviation = None
        self.Deviation = None
        self.Result = ResultStatusOption.NotComputed
        self.ReportStatus = ReportStatus.NotComputed
        self.ReportMsg = None


class DeviationAttributes(object):
    def __init__(self, diff_mode, num_dev_plus, num_dev_minus, percent_dev_plus, percent_dev_minus):
        self.DiffMode = diff_mode
        self.NumericDeviationPlus = num_dev_plus
        self.NumericDeviationMinus = num_dev_minus
        self.PercentDeviationPlus = percent_dev_plus
        self.PercentDeviatoinMinus = percent_dev_minus

class VariableAttributes(object):
    def __init__(self, variable_path, relative_path, var_type, obj_instance,container_obj=None,container_key=None):
        """
        :param variable_path: Variable full path
        :type variable_path: str
        :param relative_path: Variable relative path
        :type relative_path: str
        :param var_type: Variable type
        :param obj_instance: API instance
        """
        self.VarPath = variable_path
        self.RelativePath = relative_path
        self.VarType = var_type
        self.ApiInstance = obj_instance
        self.Container_obj = container_obj
        self.Container_key = container_key

    def GetVarFromPath(self):
        if not self.Container_obj:
            return operator.attrgetter(self.RelativePath)(self.ApiInstance)
        else:
            return self.Container_obj[self.Container_key]

class ComparatorElement(with_metaclass(ABCMeta, object)):
    def __init__(self, var_attr, expected, comp_method):
        """
        :param var_attr: Variable attributes includes full path, relative path, type and API reference
        :type var_attr: VariableAttributes
        :param expected:
        :param CompareMethod: Compare method
        :type CompareMethod: CompareMethod
        """
        self.PathToVariable = None
        self.VarAttributes = None
        self.CompareMethod = None
        #self._ApiFromOutter = None
        self.__SetElements(var_attr, expected, comp_method)

    def InitResults(self, expected):
        self.Results = CompareResults()
        self.Results.ExpectedValue = expected

    def __SetElements(self, var_attr, expected, comp_method):
        """
        :param path_to_variable: Variable full or relative path.
        :param expected: Expected result value
        :return:
        """
        function_name = self.__SetElements.__name__
        if isinstance(var_attr, VariableAttributes):
            self.VarAttributes = var_attr
        else:
            raise ComparatorArgumentError("Illegal var_attr argument. Should be from type VariableAttributes",
                                          function_name)
        
        def check_if_cant_be_compared():
            res = True
            err = ""
            supported_class_types_all_comp_method = (int,float,IntEnum)
            supported_class_types_equal = supported_class_types_all_comp_method + (str,)
            var_type = self.VarAttributes.VarType
            expected_type = type(expected)
            if var_type is expected_type or comp_method is CompareMethod.Equal and\
                    var_type in  supported_class_types_equal and\
                    expected_type in supported_class_types_equal:
                res = False
            elif isinstance(expected,supported_class_types_all_comp_method) and var_type in supported_class_types_all_comp_method:
                res = False
            if res:
                err = function_name + "The requested variable and the expected value can't be compared."
                err += "requested variable type is {} and  expected is {}".format(var_type,expected_type)
                err += "\nOnly the following types cant be compared to each other {}".format(supported_class_types_all_comp_method)
                raise ComparatorEnvironmentError(err,initiator="check_if_cant_be_compared")
        check_if_cant_be_compared()
        #self._ApiFromOutter = api_from_outter
        #self.PathToVariable = foundMatch
        self.InitResults(expected)
        self.CompareMethod = comp_method

    # def GetVarFromPath(self):
    #     return operator.attrgetter(self.PathToVariable)(self._ApiFromOutter)
    @property
    def Attributes(self):
        return self._Attributes
    
    @Attributes.setter
    def Attributes(self, value):
        """
        :param value: NumericAttributes object
        :type value: DeviationAttributes
        """

        if not isinstance(value, DeviationAttributes) and value is not None:
            raise ComparatorArgumentError("Wrong num_attr argument. Should be from type NumericAttributes",
                                          'Attributes setter')
        else:
            self._Attributes = value
            
    @abstractmethod
    def Compare(self):
        pass


class ComparatorElementBasic(ComparatorElement):
    def __init__(self, var_attr, expected, comp_method):
        super(ComparatorElementBasic, self).__init__(var_attr, expected, comp_method)

    def Compare(self):
        function_name = self.Compare.__name__
        self.Results.ActualValue = self.VarAttributes.GetVarFromPath()
        #print self.Results.ActualValue
        if self.CompareMethod == CompareMethod.Equal:
            self.__Compare_Equal()
        elif self.CompareMethod == CompareMethod.NotEqual:
            self.__Compare_NotEqual()
        else:
            raise ComparatorEnvironmentError("Compare method " + self.CompareMethod.name + "is illegal for this "
                                                                                           "variable type!",
                                             function_name)

    def ValidateRequirements(self):
        err = ""
        if self.Results.ActualValue is None:
            err = "Wrong comparator usage. Results.ActualValue member was not assigned.\
            Please, set all required members and then run Compare()."
        elif self.CompareMethod == CompareMethod.Diff:
            if self.Results.ExpectedValue == 0 and\
               (self.Attributes.PercentDeviatoinMinus is not None or self.Attributes.PercentDeviationPlus is not None):
                err = "cant calculate percentage from expected value 0, please use Numeric Deviation instead"
        if err:
            raise EnvironmentError(err)

    def __Compare_Equal(self):
        function_name = self.__Compare_Equal.__name__
        result = False
        # try:
        #     self.ValidateRequirements()
        # except EnvironmentError as e:
        #     raise ComparatorEnvironmentError(str(e), function_name)

        if self.Results.ActualValue == self.Results.ExpectedValue:
            self.Results.ReportStatus = ReportStatus.AsExpected
            self.Results.Result = ResultStatusOption.Equal
            result =  True
        else:
            self.Results.ReportStatus = ReportStatus.Unexpected
            self.Results.Result = ResultStatusOption.NotEqual
            self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                ResultStatusOption.ToString(self.Results.Result),
                ReportStatus.ToString(self.Results.ReportStatus))
        return result

    def __Compare_NotEqual(self):
        function_name = self.__Compare_NotEqual.__name__
        result = False
        # try:
        #     self.ValidateRequirements()
        # except EnvironmentError as e:
        #     raise ComparatorEnvironmentError(str(e), function_name)

        if self.Results.ActualValue != self.Results.ExpectedValue:
            self.Results.ReportStatus = ReportStatus.AsExpected
            self.Results.Result = ResultStatusOption.NotEqual
            result = True
        else:
            self.Results.ReportStatus = ReportStatus.Unexpected
            self.Results.Result = ResultStatusOption.Equal
            self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                ResultStatusOption.ToString(self.Results.Result),
                ReportStatus.ToString(self.Results.ReportStatus))
        return result


class ComparatorElementBoolean(ComparatorElementBasic):
    def __init__(self, var_attr, expected, comp_method):
        super(self.__class__, self).__init__(var_attr, expected, comp_method)


class ComparatorElementEnumerator(ComparatorElementBasic):
    def __init__(self, var_attr, expected, comp_method):
        super(self.__class__, self).__init__(var_attr, expected, comp_method)


class ComparatorElementNumerical(ComparatorElementBasic):
    def __init__(self, var_attr, expected, comp_method, num_attr=None):
        super(self.__class__, self).__init__(var_attr, expected, comp_method)
        self.Attributes = num_attr

    def Compare(self):
        self.Results.ActualValue = self.VarAttributes.GetVarFromPath()
        if self.CompareMethod == CompareMethod.Equal or self.CompareMethod == CompareMethod.NotEqual:
            super(self.__class__, self).Compare()
        elif self.CompareMethod == CompareMethod.GreaterThan:
            self.__Compare_GreaterThan()
        elif self.CompareMethod == CompareMethod.LessThan:
            self.__Compare_LessThan()
        elif self.CompareMethod == CompareMethod.GreaterOrEqual:
            self.__Compare_GreaterOrEqual()
        elif self.CompareMethod == CompareMethod.LessOrEqual:
            self.__Compare_LessOrEqual()
        elif self.CompareMethod == CompareMethod.Diff:
            self.__Compare_Diff()

    def __Compare_GreaterThan(self):
        function_name = self.__Compare_GreaterThan.__name__
        result = False
        # try:
        #     self.ValidateRequirements()
        # except EnvironmentError as e:
        #     raise ComparatorEnvironmentError(str(e), function_name)

        if self.Results.ActualValue > self.Results.ExpectedValue:
            self.Results.ReportStatus = ReportStatus.AsExpected
            self.Results.Result = ResultStatusOption.GreaterThan
            result = True
        else:
            self.Results.ReportStatus = ReportStatus.Unexpected
            self.Results.Result = ResultStatusOption.Equal if self.Results.ActualValue == self.Results.ExpectedValue \
                else ResultStatusOption.LessThan
            self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                ResultStatusOption.ToString(self.Results.Result),
                ReportStatus.ToString(self.Results.ReportStatus))

        return result

    def __Compare_LessThan(self):
        function_name = self.__Compare_LessThan.__name__
        result = False
        # try:
        #     self.ValidateRequirements()
        # except EnvironmentError as e:
        #     raise ComparatorEnvironmentError(str(e), function_name)

        if self.Results.ActualValue < self.Results.ExpectedValue:
            self.Results.ReportStatus = ReportStatus.AsExpected
            self.Results.Result = ResultStatusOption.LessThan
            result = True
        else:
            self.Results.ReportStatus = ReportStatus.Unexpected
            self.Results.Result = ResultStatusOption.Equal if self.Results.ActualValue == self.Results.ExpectedValue \
                else ResultStatusOption.GreaterThan
            self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                ResultStatusOption.ToString(self.Results.Result),
                ReportStatus.ToString(self.Results.ReportStatus))

        return result

    def __Compare_GreaterOrEqual(self):
        function_name = self.__Compare_GreaterOrEqual.__name__
        result = False
        # try:
        #     self.ValidateRequirements()
        # except EnvironmentError as e:
        #     raise ComparatorEnvironmentError(str(e), function_name)

        if self.Results.ActualValue >= self.Results.ExpectedValue:
            self.Results.ReportStatus = ReportStatus.AsExpected
            self.Results.Result = ResultStatusOption.Equal if self.Results.ActualValue == self.Results.ExpectedValue \
                else ResultStatusOption.GreaterThan
            result = True
        else:
            self.Results.ReportStatus = ReportStatus.Unexpected
            self.Results.Result = ResultStatusOption.LessThan
            self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                ResultStatusOption.ToString(self.Results.Result),
                ReportStatus.ToString(self.Results.ReportStatus))

        return result

    def __Compare_LessOrEqual(self):
        function_name = self.__Compare_LessOrEqual.__name__
        result = False
        # try:
        #     self.ValidateRequirements()
        # except EnvironmentError as e:
        #     raise ComparatorEnvironmentError(str(e), function_name)

        if self.Results.ActualValue <= self.Results.ExpectedValue:
            self.Results.ReportStatus = ReportStatus.AsExpected
            self.Results.Result = ResultStatusOption.Equal if self.Results.ActualValue == self.Results.ExpectedValue \
                else ResultStatusOption.LessThan
            result = True
        else:
            self.Results.ReportStatus = ReportStatus.Unexpected
            self.Results.Result = ResultStatusOption.GreaterThan
            self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                ResultStatusOption.ToString(self.Results.Result),
                ReportStatus.ToString(self.Results.ReportStatus))

        return result

    def __Compare_Diff(self):
        function_name = self.__Compare_LessOrEqual.__name__
        result = True
        try:
            self.ValidateRequirements()
        except EnvironmentError as e:
            raise ComparatorEnvironmentError(str(e), function_name)

        if self.Attributes.DiffMode == CompareDiffOptions.AbsDiff:
            if self.Attributes.NumericDeviationPlus is not None or self.Attributes.NumericDeviationMinus is not None:
                acceptableDeviation = self.Attributes.NumericDeviationPlus if self.Attributes.NumericDeviationPlus is not None else\
                    self.Attributes.NumericDeviationMinus
                actualDeviation = self.Results.ActualValue - self.Results.ExpectedValue
                self.Results.AcceptableDeviation = acceptableDeviation
                self.Results.Deviation = actualDeviation
            else:
                acceptableDeviation = float(self.Attributes.PercentDeviationPlus) if self.Attributes.PercentDeviationPlus is not None else\
                    float(self.Attributes.PercentDeviatoinMinus)
                actualDeviation = 100.0 * float(self.Results.ActualValue - self.Results.ExpectedValue)/ \
                                  float(self.Results.ExpectedValue)
                self.Results.AcceptableDeviation = str(acceptableDeviation) + "%"
                self.Results.Deviation = str(actualDeviation) + "%"


            if abs(actualDeviation) <= acceptableDeviation:
                self.Results.ReportStatus = ReportStatus.AsExpected
                self.Results.Result = ResultStatusOption.InRange
                result = True
            else:
                result = False
                self.Results.ReportStatus = ReportStatus.Unexpected
                self.Results.Result = ResultStatusOption.OutOfRange
                self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                    self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                    ResultStatusOption.ToString(self.Results.Result),
                    ReportStatus.ToString(self.Results.ReportStatus))
        else:
            if self.Attributes.NumericDeviationPlus is not None:
                acceptableDeviationP = self.Attributes.NumericDeviationPlus
                acceptableDeviationM = self.Attributes.NumericDeviationMinus * -1
                actualDeviation = self.Results.ActualValue - self.Results.ExpectedValue
                self.Results.AcceptableDeviation = (acceptableDeviationM, acceptableDeviationP)
                self.Results.Deviation = actualDeviation
            else:
                acceptableDeviationP = self.Attributes.PercentDeviationPlus
                acceptableDeviationM = self.Attributes.PercentDeviatoinMinus * -1
                actualDeviation = old_div(100 * float(self.Results.ActualValue - self.Results.ExpectedValue), \
                                  self.Results.ExpectedValue)
                self.Results.AcceptableDeviation = (str(acceptableDeviationM)+"%", str(acceptableDeviationP)+"%")
                self.Results.Deviation = str(actualDeviation)+"%"

            if acceptableDeviationM <= actualDeviation <= acceptableDeviationP:
                self.Results.ReportStatus = ReportStatus.AsExpected
                self.Results.Result = ResultStatusOption.InRange
                #self.Results.Deviation = actualDeviation
                result = True
            else:
                result = False
                self.Results.ReportStatus = ReportStatus.Unexpected
                self.Results.Result = ResultStatusOption.OutOfRange
                #self.Results.Deviation = actualDeviation
                self.Results.ReportMsg = "Variable: {} , actual value: {} expected: {}, result: {}, status: {}".format(
                    self.PathToVariable, self.Results.ActualValue, self.Results.ExpectedValue,
                    ResultStatusOption.ToString(self.Results.Result),
                    ReportStatus.ToString(self.Results.ReportStatus))
        return result


class Comparator(object):
    _Fail_The_Test = False
    _Numerical_Types = (int, float, IntEnum)
    _filenameToFileStrListMap = {}

    def __init__(self, json_api_instance, print_mode=PrintMode.OnlyOnFail, print_severity=PrintSeverity.High, title=None):
        """
        :param json_api_instance: Reference to JSON API command
        """
        self.API = json_api_instance
        self.PrintMode = print_mode
        self.PrintSeverity = print_severity
        self.ToBeCompared = [] # list ob objects to be compared
        self.Result = True
        self.Report_Msg = ""
        self.title = title

    @property
    def PrintSeverity(self):
        return self._PrintSeverity

    @PrintSeverity.setter
    def PrintSeverity(self, value):
        """
           :param value: Print severity (disabled/low/medium/high)
           :type value: PrintSeverity
           """
        if isinstance(value, PrintSeverity):
            self._PrintSeverity = value
        else:
            raise ComparatorArgumentError("Wrong print severity argument. Should be from type PrintSeverity",
                                             'PrintSeverity setter')

    @property
    def PrintMode(self):
        return self._PrintMode

    @PrintMode.setter
    def PrintMode(self, value):
        """
           :param value: Print mode (always/only on fail)
           :type value: PrintMode
           """
        if isinstance(value, PrintMode):
            self._PrintMode= value
        else:
            raise ComparatorArgumentError("Wrong print modew argument. Should be from type PrintMode",
                                          'PrintMode setter')

    def _Has_AbsDiff_Item(self):
        """
        :return: True if one of self items to be compared is an AbsDiff method
        :rtype: bool
        """
        res = False
        for item in self.ToBeCompared:
            if item.CompareMethod == CompareMethod.Diff:
                return True
        return False

    # @property
    # def API(self):
    #     return self._API
    #
    # @API.setter
    # def API(self, value):
    #     """
    #        :param value: CPSS LUA API instance
    #        :type value: BaseCPSSLUAClass
    #        """
    #     if isinstance(BaseCPSSLUAClass):
    #         self._API = value
    #     else:
    #         raise ComparatorArgumentError("Wrong json api instance argument. Should be a BaseCPSSLUAClass or "
    #                                          "derived",
    #                                          'API setter')

    # def AddCommonToCompareList(self, path_to_variable, expected):
    #     """
    #     :param path_to_variable: Variable full or relative path.
    #     :type path_to_variable: str
    #     :param expected: Expected result value
    #     :return:
    #     """
    #     function_name = self.AddCommonToCompareList.__name__
    #     # verify if path_to_variable is not an empty string
    #     if not isinstance(path_to_variable, str) or not path_to_variable:
    #         raise ComparatorArgumentError("Wrong path to variable argument. Should be a non-empty string",
    #                                       function_name)
    #     else:
    #         #print getattr(self.API, path_to_variable)
    #         print operator.attrgetter(path_to_variable)(self.API)

    def Equal(self, path_to_variable, expected):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :return:
        """
        function_name = self.Equal.__name__
        varAttr, varObj = self.ConfigureVariableAttributes(path_to_variable, function_name)
        # if isinstance(varObj, int) or isinstance(varObj, IntEnum) or isinstance(varObj, bool):
        newCompareElement = ComparatorElementBasic(varAttr, expected, CompareMethod.Equal)
        self.ToBeCompared.append(newCompareElement)
        # else:
        #     raise ComparatorEnvironmentError("Method " + function_name + " can\'t be applied to " + varAttr.VarType +
        #                                      ". You can use only int, enum or bool.",
        #                                      function_name)

    def NotEqual(self, path_to_variable, expected):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :return:
        """
        function_name = self.NotEqual.__name__
        varAttr, varObj = self.ConfigureVariableAttributes(path_to_variable, function_name)
        # if isinstance(varObj, int) or isinstance(varObj,float) or isinstance(varObj, IntEnum) or isinstance(varObj, \
        #         bool):
        newCompareElement = ComparatorElementBasic(varAttr, expected, CompareMethod.NotEqual)
        self.ToBeCompared.append(newCompareElement)
        # else:
        #     raise ComparatorEnvironmentError("Method " + function_name + " can\'t be applied to " + varAttr.VarType +
        #                                      ". You can use only int, float, enum or bool.",
        #                                      function_name)

    def GreaterThan(self, path_to_variable, expected):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :return:
        """
        function_name = self.GreaterThan.__name__
        varAttr, varObj = self.ConfigureVariableAttributes(path_to_variable, function_name)
        if isinstance(varObj,self._Numerical_Types) or hasattr(varObj,"__gt__"):
            newCompareElement = ComparatorElementNumerical(varAttr, expected, CompareMethod.GreaterThan)
            self.ToBeCompared.append(newCompareElement)
        else:
            raise ComparatorEnvironmentError("Method " + function_name + "can't be applied to " + varAttr.VarType +
                                             '. You can use only the following numeric types: {}'.format\
                                                 (self._Numerical_Types), function_name)

    def LessThan(self, path_to_variable, expected):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :return:
        """
        function_name = self.LessThan.__name__
        varAttr, varObj = self.ConfigureVariableAttributes(path_to_variable, function_name)
        if isinstance(varObj,self._Numerical_Types) or hasattr(varObj,"__lt__"):
            newCompareElement = ComparatorElementNumerical(varAttr, expected, CompareMethod.LessThan)
            self.ToBeCompared.append(newCompareElement)
        else:
            raise ComparatorEnvironmentError("Method " + function_name + "can't be applied to " + varAttr.VarType +
                                             '. You can use only the following numeric types: {}'.format\
                                                 (self._Numerical_Types), function_name)

    def GreaterOrEqual(self, path_to_variable, expected):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :return:
        """
        function_name = self.GreaterOrEqual.__name__
        varAttr, varObj = self.ConfigureVariableAttributes(path_to_variable, function_name)
        if isinstance(varObj,self._Numerical_Types) or hasattr(varObj,"__ge__"):
            newCompareElement = ComparatorElementNumerical(varAttr, expected, CompareMethod.GreaterOrEqual)
            self.ToBeCompared.append(newCompareElement)
        else:
            raise ComparatorEnvironmentError("Method " + function_name + "can't be applied to " + varAttr.VarType +
                                             '. You can use only the following numeric types: {}'.format\
                                                 (self._Numerical_Types), function_name)

    def LessOrEqual(self, path_to_variable, expected):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :return:
        """
        function_name = self.LessOrEqual.__name__
        varAttr, varObj = self.ConfigureVariableAttributes(path_to_variable, function_name)
        if isinstance(varObj,self._Numerical_Types) or hasattr(varObj,"__le__"):
            newCompareElement = ComparatorElementNumerical(varAttr, expected, CompareMethod.LessOrEqual)
            self.ToBeCompared.append(newCompareElement)
        else:
            raise ComparatorEnvironmentError("Method " + function_name + "can't be applied to " + varAttr.VarType +
                                             '. You can use only the following numeric types: {}'.format\
                                                 (self._Numerical_Types), function_name)

    def Diff(self, path_to_variable, expected, diff_mode=CompareDiffOptions.AbsDiff, num_deviation_plus=None,
             num_deviation_minus=None, percent_deviation_plus=None, percent_deviation_minus=None):
        """
        :param path_to_variable: Path to desired variable
        :param expected: Expected value of the desired variable
        :param diff_mode: Diff compare mode. If diff mode is 'AbsDiff' the num_deviation_plus or
        num_deviation_minus or  percent_deviation_plus or percent_deviation_minus (one of the mentioned)
         will be applied for calculation. If
        e.g. diff mode 'AbsDiff', expected 50 and you want to set the numeric deviation to 7
        obj.Diff(cls.var1, 50, CompareDiffOptions.AbsDiff, 7)
        e.g. diff mode 'AbsDiff', expected 40 and you want to set the percent deviation to 60
        obj.Diff(cls.var1, 40, CompareDiffOptions.AbsDiff, None, None, 60)
        If diff mode is 'Diff' the following pairs will be applied for calculation - (num_deviation_plus with
        num_deviation_minus) or (percent_deviation_plus with percent_deviation_minus).
        e.g. diff mode 'Diff, expected 120 and you want to set numeric deviation between -20 and +15
        obj.Diff(cls.var1, 120, CompareDiffOptions.Diff, 15, 20)
        e.g. diff mode 'Diff, expected 85 and you want to set percent deviation between -10 to 20
        obj.Diff(cls.var1, 85, CompareDiffOptions.Diff, None, None, 20.0, 10)
        :type diff_mode: CompareDiffOptions
        :param num_deviation_plus: Numeric deviation plus value
        :type num_deviation_plus: int
        :param num_deviation_minus: Numeric deviation minus value
        :type num_deviation_minus: int
        :param percent_deviation_plus: Deviation plus value in percents 0-100
        :type percent_deviation_plus: float
        :param percent_deviation_minus: Deviation plus value in percents 0-100
        :type percent_deviation_minus: float
        :return:
        """
        function_name = self.Diff.__name__
        varAttr,_ = self.ConfigureVariableAttributes(path_to_variable, function_name)
        if isinstance(diff_mode,CompareDiffOptions) and diff_mode != CompareDiffOptions.Unknown:
            if diff_mode == CompareDiffOptions.AbsDiff:
                if num_deviation_plus is None and percent_deviation_plus is None and\
                        num_deviation_minus is None and percent_deviation_minus is None:
                    raise ComparatorArgumentError("Wrong deviation argument. num_deviation_plus and "
                    "percent_deviation_plus arguments or num_deviation_minus and "
                    "percent_deviation_minus are None. In AbsDiff mode one of "
                    "these arguments must have a value.",
                                          function_name)
        else:
            raise ComparatorArgumentError("Wrong Diff mode argument. Should be from type CompareDiffOptions",
                                          function_name)

        numAttributes = DeviationAttributes(diff_mode, num_deviation_plus, num_deviation_minus, percent_deviation_plus,
                                            percent_deviation_minus)

        newCompareElement = ComparatorElementNumerical(varAttr, expected, CompareMethod.Diff,
                                                       numAttributes)
        self.ToBeCompared.append(newCompareElement)

        #self.AddToCompareList(path_to_variable, expected, CompareMethod.Diff, numAttributes)

    def AddToCompareListSt1(self, path_to_variable, expected):
        self.ConfigureVariableAttributes(path_to_variable, expected)

    def ConfigureVariableAttributes(self, path_to_variable, caller_frame):
        """
        :param path_to_variable: Variable full or relative path.
        :param expected: Expected result value
        :return:
        """
        function_name = self.ConfigureVariableAttributes.__name__

        #function_name= 'AddToCompareListSt1'

        # get the callers frame, one frame higher than ours
        init_frame = inspect.currentframe().f_back
        caller_frame = init_frame.f_back

        frame = inspect.getouterframes(init_frame)[1]
        file_str_list = []
        lineno = 0
        # If we are running inside EXE file (bundle Python app)
        # We will need to get the 'inspect' info by ourselves
        if getattr(sys, 'frozen', False):
            fi = inspect.getframeinfo(frame[0])
            full_path = self.getFrozenPath(fi.filename)
            lineno = fi.lineno - 1
            if full_path in Comparator._filenameToFileStrListMap:
                file_str_list = Comparator._filenameToFileStrListMap[full_path]
            else:
                file_str_list = open(full_path).read().splitlines()
                Comparator._filenameToFileStrListMap[full_path] = file_str_list
            string = file_str_list[lineno].strip()

        else:
            string = inspect.getframeinfo(frame[0]).code_context[0].strip()

        args = []
        if string.find('(')>=0:
            args = string[string.find('(') + 1:-1].split(',')
        i =1
        while len(args) <=1 and i <= 9:
            i += 1
            # If we are running inside EXE file (bundle Python app)
            # We will need to get the 'inspect' info by ourselves
            if getattr(sys, 'frozen', False):
                if len(file_str_list) > 0:
                    start = lineno - 1 - i//2
                    start = max(start, 1)
                    start = max(0, min(start, len(file_str_list) - i))
                    string = file_str_list[start:start + i][0].strip()
                else:
                    string = ""
            else:
                fi = inspect.getframeinfo(frame[0], i)
                string = fi.code_context[0].strip()
            args = string[string.find('(') + 1:-1].split(',')
        found_Match = args[0]

        # regExp = r"\b[\w.]*" + re.escape(caller_name) + r"\s*\(\s*([\w.]*)\s*,"
        # for cf_line in cf_lines:
        #     whatMatched = re.search(regExp, cf_line)
        #     if whatMatched:
        #         # print whatMatched.group(1)
        #         foundMatch = whatMatched.group(1)
        #         break
        #
        # if not foundMatch:
        #     raise ComparatorArgumentError("Wrong variable path format. Should be in format ([^a-zA-Z0-9_].)*",
        #                                   function_name)

        # strip unwanted spaces
        found_Match = found_Match.strip()
        # remove the first part until '.'
        foundMatch_wo_header = None
        varObj = None
        foundMatch_wo_header = found_Match.split('.', 1)[1] if found_Match.count('.') > 0 else found_Match
        # check if we don't deal with a container item
        re_lst = re.split(r"\[.+]",foundMatch_wo_header,flags=re.IGNORECASE)
        container_path = None
        container_obj = None
        key_actual_value = None
        is_internal_dict = False
        is_container = False
        if len(re_lst) >1:
            # we probably have a container path
            container_path = re_lst[0]
            is_container = True
        try:
            if is_container:
                keys_start_index_list = []
                keys_end_index_list = []
                is_key_a_variable = True
                container_obj = operator.attrgetter(container_path)(self.API)
                if isinstance(container_obj, (dict,OrderedDict,list,tuple,set,frozenset,str)):
                    key_var_name = foundMatch_wo_header[foundMatch_wo_header.find("[")+1:foundMatch_wo_header.find("]")]
                    if key_var_name.isdigit():
                        # the key is a literal number
                        is_key_a_variable = False
                        key_actual_value = int(key_var_name)
                    elif key_var_name.find("\"") > -1 or key_var_name.find("\'") > -1:
                        # probably key_var_name is a literal string
                        key_actual_value = key_var_name.replace("\"", "").replace('\"',"")
                        is_key_a_variable = False
                    if not is_key_a_variable and "__dict__" in container_path.lower():
                        # its an internal __dict__  obj
                        pattern = "__dict__[{}]".format(key_var_name)
                        replace_to = key_actual_value
                        found_Match = found_Match.replace(pattern, replace_to)
                        foundMatch_wo_header = foundMatch_wo_header.replace(pattern, replace_to)
                    if is_key_a_variable:
                        # search the key variable value in the caller_frame locals
                        key_actual_value = caller_frame.f_locals.get(key_var_name,None)

                        # replace the the foundMatch string for Printing the resolved member variable
                        pattern = replace_to = ""
                        if "__dict__" in container_path.lower():
                            # if its an internal __dict__  obj
                            pattern = "__dict__[{}]".format(key_var_name)
                            replace_to = key_actual_value
                            found_Match = found_Match.replace(pattern, replace_to)
                            foundMatch_wo_header = foundMatch_wo_header.replace(pattern, replace_to)
                        else:
                            # not an  internal dict object keep the container name
                            pattern = "[{}]".format(key_var_name)
                            replace_to = "[{}]".format(key_actual_value)
                        found_Match = found_Match.replace(pattern,replace_to)
                        foundMatch_wo_header = foundMatch_wo_header.replace(pattern,replace_to)
                        keys_start_index_list = [i for i, letter in enumerate(foundMatch_wo_header) if letter == "["]
                        keys_end_index_list = [i for i, letter in enumerate(foundMatch_wo_header) if letter == "]"]
                    if key_actual_value == 0 or key_actual_value not in [None,False]:
                        # get the actual var obj
                        varObj = container_obj[key_actual_value]
                        # if we have nested dicts in the container
                        if isinstance(varObj,dict):
                            if len(keys_start_index_list) > 1 and len(keys_end_index_list)>1:
                                for i,index in enumerate(keys_start_index_list):
                                    if i == 0:
                                        continue
                                    next_key_var_name = foundMatch_wo_header[keys_start_index_list[i]+1:keys_end_index_list[i]]
                                    key_actual_value = caller_frame.f_locals.get(next_key_var_name, None)
                                    if key_actual_value:
                                        container_obj = varObj
                                        varObj = varObj[key_actual_value]

                        if varObj is None:
                            err = "failed to obtain the key {} value from the container type {}".format(key_actual_value,type(container_obj))
                            raise AttributeError(err)
            else:
                varObj = operator.attrgetter(foundMatch_wo_header)(self.API)
                #print varObj

            return VariableAttributes(found_Match, foundMatch_wo_header, type(varObj), self.API,container_obj,key_actual_value),varObj

        except AttributeError as e:
            raise ComparatorArgumentError("{} Attribue \"{}\" not found. Error: {}".format(function_name,found_Match,str(e)),
                                          function_name)

    # If we are running inside EXE file (bundle Python app)
    # We will need to get the 'froze' path instead of the real path
    def getFrozenPath(self, f_path):
        # we are running in a bundle (e.g. 'exe' file)
        # so we must change the root dir to be the "Temp one"
        tmp_dir = getattr(sys, '_MEIPASS', "c:\\")
        project_name = "Python_Platform_Validation_Tests"
        pnl = len(project_name)
        pni = f_path.rfind(project_name)
        path = f_path[pni + pnl + 1:]
        path = os.path.join(tmp_dir, path)
        return path

    def Compare(self):

        # Need for stoping the test from another thread
        if Comparator._Fail_The_Test:
            self.Result = False
            return False

        for item in self.ToBeCompared:
            item.Compare()
            if self.Result == True:
                if item.Results.ReportStatus == ReportStatus.Unexpected:
                    self.Result = False
        # always create report
        self.CreateReport()
        # Verify if there is a need to print
        if self.PrintMode == PrintMode.Always:
            self.PrintReport()
        elif self.PrintMode == PrintMode.OnlyOnFail and not self.Result:
            self.PrintReport()
        return self.Result

    def PrintReport(self):
        if self.Result:
            GlobalLogger.logger.debug(self.Report_Msg)
        else:
            GlobalLogger.logger.error(self.Report_Msg)
    
    def CreateReport(self):
        """
        :return: tuple of )list,list_has_diff_items) - each element of returned list is a list of strings[compared
        field name,field actual value,field expected value,result,<allowed deviation>,<actual deviation>]
        :rtype:
        """
        reportTable = PrettyTable()
        ret_list = []
        has_diff_item = self._Has_AbsDiff_Item()
        if self.PrintSeverity == PrintSeverity.Low:
            reportTable.field_names = ["Variable Name", "Method", "Actual Value", "Expected Value", "Result", "Status"]
            for item in self.ToBeCompared:
                row = [item.VarAttributes.VarPath, CompareMethod.ToString(item.CompareMethod), item.Results.ActualValue,
                       item.Results.ExpectedValue, ReportStatus.ToString(item.Results.ReportStatus)]
                ret_row = [item.VarAttributes.VarPath.split(".")[-1],item.Results.ActualValue,item.Results.ExpectedValue]
                ret_list.append(ret_row)
                reportTable.add_row(row)
        elif self.PrintSeverity == PrintSeverity.Medium:
            reportTable.field_names = ["Variable Name", "Method", "Actual Value", "Expected Value", "Result", "Status"]
            for item in self.ToBeCompared:
                row = [item.VarAttributes.VarPath, CompareMethod.ToString(item.CompareMethod),
                       item.Results.ActualValue, item.Results.ExpectedValue,
                       ResultStatusOption.ToString(item.Results.Result), ReportStatus.ToString(
                        item.Results.ReportStatus)]
                ret_row = [item.VarAttributes.VarPath.split(".")[-1],item.Results.ActualValue,item.Results.ExpectedValue]
                ret_list.append(ret_row)
                reportTable.add_row(row)
        else:
            if has_diff_item:
                reportTable.field_names = [
                    "Variable Name", "Method", "Actual Value", "Expected Value", "Result", "Status",
                    "Deviation Method", "Actual Deviation", "Acceptable Deviation"]
            else:
                reportTable.field_names = ["Variable Name","Method","Actual Value","Expected Value", "Result", "Status"]
            for item in self.ToBeCompared:
                if isinstance(item, ComparatorElementNumerical) and has_diff_item:
                    addAttributes = [CompareDiffOptions.ToString(item.Attributes.DiffMode), item.Results.Deviation,
                                     item.Results.AcceptableDeviation]
                else:
                    addAttributes = [None, None, None]
                row = [item.VarAttributes.VarPath,  CompareMethod.ToString(item.CompareMethod),
                       item.Results.ActualValue, item.Results.ExpectedValue,
                       ResultStatusOption.ToString(item.Results.Result), ReportStatus.ToString(
                        item.Results.ReportStatus)]
                ret_row = [item.VarAttributes.VarPath.split(".")[-1],item.Results.ActualValue,item.Results.ExpectedValue,
                           True if item.Results.ReportStatus is ReportStatus.AsExpected else False]
                if has_diff_item:
                    row += addAttributes
                    ret_row += [item.Results.AcceptableDeviation,item.Results.Deviation]
                ret_list.append(ret_row)
                reportTable.add_row(row)
        self.Report_Msg = "\n" + reportTable.get_string(title=self.API.__class__.__name__ if not self.title else self.title)
        return ret_list,has_diff_item
