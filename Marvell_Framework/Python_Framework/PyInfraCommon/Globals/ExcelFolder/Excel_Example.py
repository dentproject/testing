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

from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
__author__ = 'Erez Ashkenazi'

from . import Excel
from copy import deepcopy, copy
import re

class ExcelDataLoad(object):

    def __init__(self):
        """
        Constructor
        :return:
        """
        self.EX = Excel.Excel()

    def set_active_file(self, file_path):
        """
        set the excel file the class will work on
        :param file_path:
        :return:
        """
        self.EX.set_active_workbook(file_path)

    def LoadBoards(self, i_BoardList=None):
        """
        This method will load all board needed for this test
        :param BoardsList: set specific board (by board model or board name)if None get all boards in the working sheet
        :param worksheet:
        :return: board dict
        """
        Boards = {}
        worksheet = 'Board_Data'
        self.EX.set_active_worksheet(sheet_name=worksheet)
        All_Boards = self.EX.get_data_by_column('A', 1, 1)
        Headers = self.EX.get_data_by_row(1, 1, 1)
        o_BoardsList=self._Load_Table(All_Boards, Headers)

        if i_BoardList:
            BoardsList = i_BoardList
            if type(i_BoardList) != list:
                BoardsList = [i_BoardList]
            for i_board in BoardsList:
                for board in o_BoardsList:
                    if o_BoardsList[board]['Marvell_Board_Model'].lower() in i_board.lower() or board.lower() == i_board.lower():
                        Boards[board]=o_BoardsList[board]
        else:
            return o_BoardsList

        return Boards

    def get_topology(self,i_worksheet, i_DataToGet, i_column_key=None):
        """
        get a topology from a specific sheet by input data
        :param i_worksheet:
        :param column_search: the column in which the dict main key will be set by
        :param DataToGet: the data set we want to get as a dictionary
        :return: the dictionary of the input data
        """
        delimiter=','
        if type(i_DataToGet) == str or type(i_DataToGet) == int:
            i_DataToGet = str(i_DataToGet)

        DataToGet = i_DataToGet
        # if type(i_DataToGet) == int:
        #     DataToGet = [i_DataToGet]

        self.EX.set_active_worksheet(sheet_name=i_worksheet)
        DataToGet = DataToGet.split(delimiter)
        Headers = self.EX.get_data_by_row(1, 1, 1)
        Topology = self._Load_Table(DataToGet, Headers)
        if i_column_key:
            Topology = self.switch_main_key(Topology, i_column_key)
        return Topology

    def switch_main_key(self,i_dict, new_main_key):
        """
        get a dict and switch it's main keys by new values from sub dict keys.
        :param i_dict: the dictionary we want to switch keys inside
        :param new_main_key: the value to be used as the main key in the new dict
        :return: "same dict" with updated key name
        """
        temp = {}

        for key, value in i_dict.items():
            if new_main_key not in value:
                raise ('error when trying to get the main key of topolopy from sheet name={sheetname} the key={keytomap} doesn"t exist')
            temp[i_dict[key][new_main_key]]=i_dict.get(key)
        return temp

    def topology_to_values(self, i_column_key=None, **kwargs):
        """
        :param column_search: the column in which the dict main key will be set by
        :param kwargs: Networking={'0':{}} , Networking is the tab o search in, and it's data will be
        :return: values of the input topologies
        """
        name=next(iter(kwargs.items()))
        ret=self.get_topology(i_worksheet=name[0], i_DataToGet=name[1], i_column_key=i_column_key)
        return ret

    def parse_sheet_and_Topology(self,i_topology):
        temp={}
        format='(.*)(_)([0-9]+)' #sheetname_topology
        r=re.match(format,i_topology )
        sheetname = r.group(1)
        topo=r.group(3)
        data=self.get_topology(sheetname,topo)
        data[sheetname]=data.pop(topo)
        return data

    def LoadTest(self,i_TestList=None):
        o_Test={}
        worksheet = 'Tests_Defaults'
        self.EX.set_active_worksheet(sheet_name=worksheet)
        All_Tests = self.EX.get_data_by_column('A', 1, 1)
        Headers = self.EX.get_data_by_row(1, 1, 1)
        o_TestsList = self._Load_Table(All_Tests, Headers)
        if i_TestList:
            if type(i_TestList) != list:
                i_TestList = [i_TestList]
            for test in i_TestList:
                test = test.strip()
                if test in o_TestsList:
                    o_Test[test]=deepcopy(o_TestsList[test])
            o_TestsList=deepcopy(o_Test)
        return o_TestsList

    def load_env_data(self,worksheet='Environment_Data'):
        """
        The Function Loads All The Environment Data Of
        The Lab From WorkSheet - "Environment_Data"
        :param worksheet:
        :return:
        """
        self.EX.set_active_worksheet(sheet_name=worksheet)
        Devices=self.EX.get_data_by_column('A', 1, 1)
        Headers=self.EX.get_data_by_row(1, 1, 1)
        Env_Data=self._Load_Table(Devices,Headers)
        return Env_Data

    def load_ovelapping_rows(self,worksheet,**kwargs):
        """
        :param worksheet: the worksheet to work on
        :param kwargs:
        :return:
        """
        self.EX.set_active_worksheet(sheet_name=worksheet)
        Headers = self.EX.get_data_by_row(1, 0, 1)
        cell_to_cut_by = Headers.index('Board')
        Headers = Headers[:cell_to_cut_by]
        overlapping_rows=self.EX.find_all_ovelapping_rows(**kwargs)
        Data={}
        for idx,item in enumerate(overlapping_rows):
            Data[idx]=self.EX.get_data_by_row(item,0,1,remove_vales_at_end=cell_to_cut_by)
        #Convert to list of list
        list_Data=[]
        for item,value in Data.items():
            list_Data.append(value)
        #sort the list based on location inside , sorted by all locations when location 0 is first location 1 is second and etc
        Data.clear()
        Data['Headers']=Headers
        Data['Iterations'] = sorted(list_Data)

        if len(Data['Iterations']) == 0:
            Data['Iterations'] = None

        return Data

    @staticmethod
    def choice_defaults_or_override_values(self, defaults_values, override_values):
        """
        The Funcion Takes The 'Override_Default_Values' values ( If They Exist)
        and set them to 'Features_Values' (See Explanation Below).

        Practical Explanation:
        After This Function All The Parametres Of the Test Will Be In The
        'Features_Value', This Dictionary Will Be Updated.
        If The Default Values Have Been Changed We Will See The Proper Value
        In This Section

        :param All_Test_To_Run:
        :param defaults_values:
        :return:
        """


        temp_defaults_value = deepcopy(defaults_values)
        dict_to_override_defaults = deepcopy(override_values)
        for key in temp_defaults_value:
            if key in dict_to_override_defaults:
                if len(dict_to_override_defaults[key])>0:
                   temp_defaults_value[key]=dict_to_override_defaults[key]

        return temp_defaults_value

    def load_output_results(self, i_All_Tests, i_worksheet=None):
        """
        The Current Function Takes The worksheet - 'Output_Results_Structure'
        and add each OUTPUT format for each test as List

        :param worksheet:
        :param id:
        :return:
        """
        All_Tests = deepcopy(i_All_Tests)
        worksheet = i_worksheet
        self.EX.set_active_worksheet(sheet_name = worksheet)
        for test in All_Tests:
            i_All_Tests.remove(test)
            test_name, test_value = next(iter(test.items()))
            output=self.EX.get_data_by_row(test_name,2,1)
            test_value[worksheet]=deepcopy(output)
            i_All_Tests.append({test_name: deepcopy(test_value)})

        return i_All_Tests

    def load_expected_results(self, i_All_Tests, i_worksheet = None,i_Test_Names=None):
        """
        The Current Function Takes The worksheet - 'Expected Results'
        and add each results format for each test as Dict

        :param i_worksheet:
        :param id:
        :return:
        """
        All_Tests=deepcopy(i_All_Tests)
        self.EX.set_active_worksheet(sheet_name=i_worksheet)
        expected_results=self.create_dict_from_sheet(i_sheet_name = i_worksheet, i_All_Rows_In_Main_Column=i_Test_Names)
        for test in All_Tests:
            i_All_Tests.remove(test)
            test_name, test_value = next(iter(test.items()))
            test_value[i_worksheet]=deepcopy(expected_results[test_name])
            i_All_Tests.append({test_name: deepcopy(test_value)})

        return i_All_Tests

    def create_dict_from_sheet(self, i_sheet_name=None, i_All_Rows_In_Main_Column=None, i_Main_Column=None):
        """
        Create a dictionary out of the current sheet by the following format:
        first cell Row - Main Key
        Coll - Keys in dict
        Cell - Value of keys
        :return: dict () format: {name_of_each_row:num_of_appearences:{col:value}
        """
        if i_Main_Column is None:
            raise  Exception("Please supply main column")
        Row_Names =i_All_Rows_In_Main_Column
        if i_All_Rows_In_Main_Column != None:
            if i_All_Rows_In_Main_Column == str:
                Row_Names = [i_All_Rows_In_Main_Column]
            else:
                Row_Names=i_All_Rows_In_Main_Column
        self.EX.set_active_worksheet(sheet_name=i_sheet_name)
        Headers = self.EX.get_data_by_row(1, 0, 1)
        Main_Dict={}
        tmp_dict={}
        max_lines=int(self.EX.WS.max_row)
        start = 0 # internal counter for number of testID with the same name
        for row in range(2,max_lines+1):
            #create the dic main key for keys, from Headers
            tmp_dict=next(iter(self._Load_Table(row, Headers).values()))
            if Row_Names != None and tmp_dict[i_Main_Column] not in Row_Names:
                continue
            if tmp_dict.__len__ ()== 0: #No more lines with info inside
                break
            if tmp_dict[i_Main_Column] not in Main_Dict:
                start=1
                Main_Dict[tmp_dict[i_Main_Column]]={}
            else: #advance the counter of the items in of the same test
                start += 1
            Main_Dict[tmp_dict[i_Main_Column]][start]=copy(tmp_dict)
        return Main_Dict

    def create_List_from_sheet(self, sheet_name):
        """
        Create a dictionary out of the current sheet by the following formula (as for now it only support expected results when we have mutiple times the same name)
        first cell Row - Main Key
        Coll - Keys in dict
        Cell - Value of keys
        :return:
        """

        self.EX.set_active_worksheet(sheet_name=sheet_name)
        Headers = self.EX.get_data_by_row(1, 0, 1)
        Main_Dict={}
        tmp_dict={}
        max_lines=int(self.EX.WS.max_row)
        start = 0 # internal counter for number of testID with the same name
        for row in range(2,max_lines+1):
            #create the dic main key for keys, from Headers
            tmp_dict=next(iter(self._Load_Table(row, Headers).values()))
            if tmp_dict.__len__ ()== 0: #No more lines with info inside
                break
            if tmp_dict['TestID'] not in Main_Dict:
                start=1
                Main_Dict[tmp_dict['TestID']]={}
            else: #advance the counter of the items in of the same test
                start += 1
            Main_Dict[tmp_dict['TestID']][start]=copy(tmp_dict)
        return Main_Dict

    def _load_test_defaults(self, worksheet = 'Test_defaults'):
        """
        The Current Function Takes All The Data From Worksheet - 'Test_Defaults'
        and Creates a Dictionary by TestId and All The Default Params For That Test
        :param worksheet:
        :param id:
        :return:
        """
        self.EX.set_active_worksheet(sheet_name = worksheet)
        id=self.EX.get_data_by_column('A', 1, 1)
        Headers=self.EX.get_data_by_row(1, 1, 1)
        Tests_Defaults=self._Load_Table(id,Headers)
        return Tests_Defaults
        """
            id=[]
        self.EX.set_active_worksheet(sheet_name = worksheet)
        id_full=self.EX.get_data_by_column('A', 1, 0)
        for i in id_full:
            if i.value!=None:
                id.append(i.row)
        Headers=self.EX.get_data_by_row(1, 1, 1)
        Tests_Defaults=self._Load_Table(id,Headers,skip_at_first=1)
        for i in xrange(id.__len__()):
            if Tests_Defaults.has_key(id_full[i].value):
                temp=Tests_Defaults.pop(id_full[i].value)
                Tests_Defaults[id_full[i].value]={}
                Tests_Defaults[id_full[i].value][Tests_Defaults[id_full[i].value].__len__()]=deepcopy(temp)
                Tests_Defaults[id_full[i].value][Tests_Defaults[id_full[i].value].__len__()]=Tests_Defaults.pop(id[i])
            else:
                Tests_Defaults[id_full[i].value] = Tests_Defaults.pop(id[i])
        return Tests_Defaults
        """

    def _Load_Table(self, id, header):
        """
        The Function Gets All The Data From Worksheet That It was Called.
        The Function Creates A Dictionary by The Next Format:
        Row - Main Key
        Coll - Secondary Key
        Cell - Value of Secondary key

        :param Key:
        :return: Dictionary of the content
        """
        if type(id)==str:
            id=str(id)
        if type(id)==str or type(id)==int:
            id=[id]
        Table={}
        Table_Info={}
        # for num,item in enumerate(id):
        for item in id:
            #TODO: if item is int and we want to skip data at first, we should add
            info_sub=self.EX.get_data_by_row(item,0 if type(item)==int else 1 , 1)
            for itr,head in enumerate(header):
                try:
                    Table_Info[header[itr]]=info_sub[itr]
                except IndexError:
                    Table_Info[header[itr]]=None
            Table[item]=deepcopy(Table_Info)
            Table_Info.clear()
        return Table

    def _load_board_topologies(self, All_Tests):
        """

        :param All_Tests:
        :param worksheet:
        :return:
        """
        Topologies=['Uboot']
        for testid in All_Tests:
            for board in All_Tests[testid]['Board_Data']:  # get the data from all boards in the env
                for topo in Topologies:
                    if topo not in All_Tests[testid]['Board_Data'][board]:  # check if topology exists
                        continue
                    if All_Tests[testid]['Board_Data'][All_Tests[testid]['Org_Board']][topo]==None: #Skips empty topologies
                        continue
                    self.EX.set_active_worksheet(sheet_name=topo)
                    Topo_Data={}
                    if topo not in Topo_Data:
                        Topo_Data[topo]={}
                    Data=str(All_Tests[testid]['Board_Data'][board][topo]).split(',')
                    Headers = self.EX.get_data_by_row(1, 1, 1)
                    for item in Data:
                        info_of_row=next(iter(self._Load_Table(item,Headers).values()))
                        Topo_Data[topo][info_of_row['Name']]=info_of_row
                    All_Tests[testid]['Board_Data'][board][topo]=deepcopy(next(iter(Topo_Data.values())))
        return All_Tests

    def _board_data(self,All_Tests):
        """
        The Funcion Extracts All The Data About The Boards That are Active In The Current Test only,
        From Worksheet - 'Board_Data'
        Adding The Data To The "All_Tests" Dictionary

        :param Tests:
        :return:
        """
        worksheet = 'Board_Data'
        self.EX.set_active_worksheet(sheet_name=worksheet)
        Headers=self.EX.get_data_by_row(1, 1, 1)
        for testid in All_Tests:
            Devices = All_Tests[testid]['Test_Devices'].split(',')
            # Devices=[All_Tests[testid]['Org_Board'],All_Tests[testid]['Ter_Board']]
            data=self._Load_Table(Devices,Headers)
            # print data
            All_Tests[testid]['Board_Data']=deepcopy(data)
        # print All_Tests
        return All_Tests

    def _load_Topology(self, All_Tests):
        """
        if we have test defaults with couple of topologies we want to extract all the values from those topologies
        :param All_Tests:
        :return:
        """
        sheets_in_excel=self.EX.sheets_in_workbook() #get all sheets names in the file
        for testid in All_Tests:
            Features_Value=All_Tests[testid].pop('Features_Value')
            Features_Value_For_Iterations={}
            Features_Value_Not_Iterations = {}
            for feature in Features_Value:
                if Features_Value[feature]==None: #skip empty topologies
                    continue
                feature_wo_priority=str(feature).partition('|')[0] #to cut the priority from the name in order to compare with the tab name in excel
                if str(feature_wo_priority) in sheets_in_excel:
                    list_of_topo=str(Features_Value[feature]).split(',')
                    list_of_topo_replaced=[]
                    self.EX.set_active_worksheet(feature_wo_priority) # change active sheet to the sheet feature for topology extraction
                    for topo in list_of_topo: #get every topologies real vaule
                        if str(feature).partition('|')[1]=='|': #Do it if we have priority in the name
                            list_of_topo_replaced.append(self.EX.get_cell_value(str(topo),str(feature_wo_priority)))
                            Features_Value_For_Iterations[feature] = list_of_topo_replaced  # return the new extracted values to the All_test
                        else: #str(feature).partition('|')[1] == '' and feature_wo_priority in ['Networking']: #we dont have priority in the name
                            if feature not in Features_Value_Not_Iterations:
                                Features_Value_Not_Iterations[feature]={}
                            Topology_wo_priority = {}
                            Headers = self.EX.get_data_by_row(1, 1, 1)
                            Topology_wo_priority=self._Load_Table(topo,Headers)
                            Topology_wo_priority=next(iter(Topology_wo_priority.values()))
                            if feature_wo_priority in ['Networking']:
                                Features_Value_Not_Iterations[feature][Topology_wo_priority['Port_Name']]=deepcopy(Topology_wo_priority)
                            else:
                                Features_Value_Not_Iterations[feature][Topology_wo_priority['Name']] = deepcopy(
                                    Topology_wo_priority)
            All_Tests[testid]['Features'] = deepcopy(Features_Value_Not_Iterations)
            All_Tests[testid]['Features_For_Iteration'] = deepcopy(Features_Value_For_Iterations)
        return All_Tests

    def merge_dicts(self, *dict_args):
        """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
        """
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result

    # TODO: Can be deleted
    """
    def All_Tests_Set_To_Run(self):

        The Function Gets All The TestsId From WorkSheet 'Test_Run'
        Where The Value In Collumn 'Run' Is 1
        And Creates a Dictionary where The TestId Is Main key,
        Each parameter is secondary key and the value of the parameter
        is the value of the dictionary

        :param run_value:
        :param worksheet:
        :return: Tests set to run, TestID# as List

        run_value = 'Run'
        worksheet = 'Test_Run'
        self.EX.set_active_worksheet(sheet_name = worksheet)
        col=self.EX.get_data_by_column(run_value, remove_values_at_start=2)
        id=[]
        for cell in col:
            if cell.value==1:
                id.append(self.EX.get_cell_value(cell.row,'TestID'))
        headers=self.EX.get_data_by_row(2,1,1)
        Tests=self._Load_Table(id,headers)

        #Create a dict out of 'Override_Default_Values'
        dict_of_override_defaults={}
        for id in Tests:
            override_default_values=Tests[id].pop('Override_Default_Test_Values').replace('\n','').split('#')
            for item in override_default_values:
                if len(item) > 0:
                    temp=item.partition('=')
                    dict_of_override_defaults[temp[0]]=temp[2]
            Tests[id]['Override_Default_Test_Values']=deepcopy(dict_of_override_defaults)
            dict_of_override_defaults.clear()

        #Override the defaults in every test if needed
        Tests_default = self._load_test_defaults()
        Tests = self._set_defaults_or_override_values(Tests_default,Tests)
        Tests = self.load_output_results(Tests)
        Tests = self._board_data(Tests)
        Tests = self._load_Topology(Tests) # Load test topologies only if it exists
        Tests = self._load_Active_TG_Data(Tests) # Load Traffic generator info only if (it exists)
        Tests = self.load_expected_results(Tests) # Load the test expected results tab for each active test
        # Tests = self._load_board_topologies(Tests)

        return Tests

    def _load_Active_TG_Data(self, All_Tests, worksheet='Traffic_Generator'):
        If we have a Traffic Generator in the Test we'll get all its data.
        :param Org_Board:
        :param Ter_Board:
        :param Board_Data:
        :param worksheet:
        :return: All tests with updated Traffic generator info(if Exists)

        for testid in All_Tests:
                for board in All_Tests[testid]['Board_Data']:
                    TG_Ports=['TG_Lan_Copper','TG_Wan_Copper','TG_Lan_Fiber','TG_Wan_Fiber']
                    TG_Ports_Len=TG_Ports.__len__()
                    TG_Ports_Active = []

                    for port in TG_Ports:
                        if not All_Tests[testid]['Board_Data'][board].has_key(port):
                            TG_Ports_Len -= 1
                        elif All_Tests[testid]['Board_Data'][board][port] != None:
                            TG_Ports_Active.append(port)
                    if TG_Ports_Len == 0 or TG_Ports_Active.__len__() == 0:
                        return All_Tests

                    self.EX.set_active_worksheet(sheet_name=worksheet)
                    TG = {}
                    Headers = self.EX.get_data_by_row(1, 1, 1)
                    for port in TG_Ports_Active:
                        TG[port]=str(All_Tests[testid]['Board_Data'][board][port])
                        TG[port]=self._Load_Table(TG[port],Headers).values().pop()

                    All_Tests[testid]['Traffic_Generator']=deepcopy(TG)

        return All_Tests

    def _set_defaults_or_override_values(self,defaults_value,All_Test_To_Run):

        The Funcion Takes The 'Override_Default_Values' values ( If They Exist)
        and set them to 'Features_Values' (See Explanation Below).

        Practical Explanation:
        After This Function All The Parametres Of the Test Will Be In The
        'Features_Value', This Dictionary Will Be Updated.
        If The Default Values Have Been Changed We Will See The Proper Value
        In This Section

        :param All_Test_To_Run:
        :param defaults_value:
        :return:

        for id in All_Test_To_Run:
            temp_defaults_value = defaults_value[id]
            dict_to_override_defaults = All_Test_To_Run[id].pop('Override_Default_Test_Values')
            for key in temp_defaults_value:
                if dict_to_override_defaults.has_key(key):
                    if len(dict_to_override_defaults[key])>0:
                       temp_defaults_value[key]=dict_to_override_defaults[key]
            All_Test_To_Run[id]['Features_Value']=deepcopy(temp_defaults_value)
        return All_Test_To_Run

    def set_active_tg_ports(self, i_network=None, i_TG=None, All_Tests=None):

        #Set the active networking ports in the test
        2 will be choosen: Lan + Wan
        :param network:
        :param TG:
        :param All_Tests:
        :return: active tg according to networking

        ret = {}
        Network_Return={}
        TG_Return = {}
        if All_Tests:
            return
            # for testid in All_Tests:
            #     for board in All_Tests[testid]['Board_Data']:
            #
            #         if not All_Tests[testid][board].has_key('Traffic_Generator'):
            #
            #             networking=All_Tests[testid]['Features']['Networking'].keys()
            #             TG=All_Tests[testid]['Traffic_Generator'].keys()
        TG = deepcopy(i_TG)
        networking = deepcopy(i_network)
        for tg_port in i_TG:
            for nw_port in networking:
                if nw_port in tg_port:
                    # TG_Active.append(tg_port)
                    if 'Lan' in tg_port:
                        TG_Return['Lan']=TG.pop(tg_port)
                    else:
                        TG_Return['Wan'] = TG.pop(tg_port)

        for nw_port in networking:
            if 'Lan' in nw_port:
                Network_Return['Lan']=deepcopy(networking[nw_port])
            elif 'Wan' in nw_port:
                Network_Return['Wan']=deepcopy(networking[nw_port])
        ret['TG'] = TG_Return
        ret['Net'] = Network_Return
        return ret
    """

if __name__=='__main__':
    from pprint import pprint
    Linux_Excel_CDAL='/home/erezas/trash/mmp_automation/Test_Files/Test_Run_Params_CDAL.xlsx'
    Linux_Excel_Benchmark_Test_Run='/media/local/users/erezas/Automation-devel/Test_Files/Test_Run_Benchmark.xlsx'
    Linux_Excel_Benchmark_Test_Defaults='/media/local/users/erezas/Automation-devel/Test_Files/Test_Defaults_Benchmark-develop.xlsx'
    Linux_Excel_Benchmark_Board = '/media/local/users/erezas/Automation-devel/Test_Files/Board_Data.xlsx'
    Linux_Excel_Test_Iterations = '/media/local/users/erezas/Automation-devel/artifacts/BenchMark TG Ixia-2017_12_25-11_40/Config_Files/Test_Iteration_Benchmark.xlsx'
    Windows_Excel_File="C:\GITAlexZemtzov\mmp_automation\Test_Files\Iperf_Test.xlsx"
    Traffic_Generator=\
    {'TG_Lan_Copper':
        {u'Conf_File_Name': None,
        u'Description': u'Ixia_Slot-1-Port-1',
        u'Device_Ip': u'10.5.210.211',
        u'Port_Number': 0,
        u'Port_Rate': u'1G',
        u'Port_Type': u'Copper',
        u'Slot_Number': 0},
    'TG_Lan_Fiber': {u'Conf_File_Name': None,
        u'Description': u'Ixia_Slot-8-Port-5',
        u'Device_Ip': u'10.5.210.35',
        u'Port_Number': 4,
        u'Port_Rate': u'10G',
        u'Port_Type': u'Fiber',
        u'Slot_Number': 7},
    'TG_Wan_Copper': {u'Conf_File_Name': None,
        u'Description': u'Ixia_Slot-1-Port-2',
        u'Device_Ip': u'10.5.210.211',
        u'Port_Number': 1,
        u'Port_Rate': u'1G',
        u'Port_Type': u'Copper',
        u'Slot_Number': 0},
    'TG_Wan_Fiber':
        {u'Conf_File_Name': None,
        u'Description': u'Ixia_Slot-8-Port-6',
        u'Device_Ip': u'10.5.210.35',
        u'Port_Number': 5,
        u'Port_Rate': u'10G',
        u'Port_Type': u'Fiber',
        u'Slot_Number': 7}}
    Networking={u'Lan_Copper': {u'Board': 'DB-88F8040-MODULAR',
                                   u'Description': None,
                                   u'Port': u'eth3',
                                   u'Port_Ip_Addr': u'192.168.1.254',
                                   u'Port_Mac_Addr': u'00:00:00:00:00:05',
                                   u'Port_Name': u'Lan_Copper',
                                   u'Port_Rate': u'1G',
                                   u'Port_Type': u'Copper',
                                   u'TG_Port_Ip_Addr': u'192.168.1.1',
                                   u'TG_Port_Mac_Addr': u'00:11:22:33:44:5F'},
                   u'Wan_Fiber': {u'Board': 'DB-88F8040-MODULAR',
                                  u'Description': None,
                                  u'Port': u'eth2',
                                  u'Port_Ip_Addr': u'1.1.1.254',
                                  u'Port_Mac_Addr': u'00:00:00:00:00:03',
                                  u'Port_Name': u'Wan_Fiber',
                                  u'Port_Rate': u'10G',
                                  u'Port_Type': u'Fiber',
                                  u'TG_Port_Ip_Addr': u'1.1.1.1',
                                  u'TG_Port_Mac_Addr': u'00:99:88:77:66:5F'}}
    # u'Lan_Fiber': {u'Board': 'DB-88F8040-MODULAR',
    #                u'Description': None,
    #                u'Port': u'eth0',
    #                u'Port_Ip_Addr': u'192.168.1.254',
    #                u'Port_Mac_Addr': u'00:00:00:00:00:05',
    #                u'Port_Name': u'Lan_Fiber',
    #                u'Port_Rate': u'10G',
    #                u'Port_Type': u'Fiber',
    #                u'TG_Port_Ip_Addr': u'192.168.1.1',
    #                u'TG_Port_Mac_Addr': u'00:11:22:33:44:5F'},
    # u'Wan_Copper': {u'Board': 'DB-88F8040-MODULAR',
    #                 u'Description': None,
    #                 u'Port': u'eth1',
    #                 u'Port_Ip_Addr': u'1.1.1.254',
    #                 u'Port_Mac_Addr': u'00:00:00:00:00:03',
    #                 u'Port_Name': u'Wan_Copper',
    #                 u'Port_Rate': u'1G',
    #                 u'Port_Type': u'Copper',
    #                 u'TG_Port_Ip_Addr': u'1.1.1.1',
    #                 u'TG_Port_Mac_Addr': u'00:99:88:77:66:5F'},
    LN=ExcelDataLoad()
    LN.set_active_file(Linux_Excel_Test_Iterations)
    data=LN.load_ovelapping_rows(worksheet='KS-L2-FWD',Board='DB-88F8040-MODULAR',gerrit='1')#,nightly='1')
    pprint(data)
    RO=RobotLoadExcel()
    # port=RO._get_port(['10G',None],1)
    # LN.set_active_file(Linux_Excel_Benchmark_Test)
    # Tests_To_Run = LN.All_Tests_Set_To_Run()
    #new_top=LN._parse_sheet_and_Topology('Traffic_Generator_100')
    #LN._switch_main_key()
    # run=RO.LoadTestRun(Linux_Excel_Benchmark_Test_develop)
    # bo=RO.LodadBoardData(Linux_Excel_Benchmark_Board)
    # te=RO.LoadTestData(Linux_Excel_Benchmark_Test_develop)
    # bo=LN.LoadBoards()#i_BoardList='DB-88F8040-MODULAR')
    tests=RO.NET_BM_TestStart(i_Board_Config_FileName=Linux_Excel_Benchmark_Board, i_Test_Defaults_Config_FileName=Linux_Excel_Benchmark_Test_Defaults, i_Test_Run_Config_FileName=Linux_Excel_Benchmark_Test_Run, i_test_Run_Worksheet='7040')
    # pprint(run)
    # pprint(bo)
    pprint(tests)
    #net=LN._get_topology('Networking',bo['DB-8040-A1-10.5.237.20']['Networking'], 'Port_Name')
    net=LN.topology_to_values(i_column_key='Port_Name', Networking='0,1,2')
    r=LN.set_active_tg_ports(i_network=Networking,i_TG=Traffic_Generator)
    # A=LN._create_dict_from_sheet()
    Tests_To_Run = LN.All_Tests_Set_To_Run()
    #print 'TestID# Are:', TestID
    print("The test to runs are =\n")
    pprint (Tests_To_Run)
    # device=LN.load_env_data()
    # print "DEVICE:"
    # pprint (device)
    # env_data=LN.load_env_data()
    # print "Env_Data_Is\:n"
    # pprint (env_data)
    # TG=LN._load_Active_TG_Data(Tests_To_Run)
    # print "TG_Data_Is\:n"
    # pprint (TG)