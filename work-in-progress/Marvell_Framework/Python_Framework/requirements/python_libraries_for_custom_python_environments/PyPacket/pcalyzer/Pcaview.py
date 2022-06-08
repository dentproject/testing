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

import copy
import subprocess
import os
from os.path import exists

from PyPacket.pcalyzer.shark.TSHARK_ENUMS import TSHARK_ENUMS
from PyPacket.pcalyzer.shark.TsharkCommander import tsharkCommandBuilder
from PyPacket.pcalyzer.Common import packetFieldsResultEntry

class pcaview(object):
    def __init__(self, name, filter=None, fields=None,workDir=""):
        self.name = name
        self._parent = None #type: pcalyzer
        self._wsFilter = filter
        self._requestedFields = list(fields)
        self._result = [] #type: list[packetFieldsResultEntry]
        self._outFile = os.path.join(workDir,'txt'+self.name+'.txt')
        self.delimeter = '~'
        self.default_fields = ['frame.number','frame.time_relative','frame.len']
        self._pcap_file = None
        self._index_filter = None
        self._current_pcap_file = ''

    @property
    def current_pcap_file(self):
        return self._pcap_file if self._pcap_file else self._parent._pcap_file

    @property
    def rFilter(self,):
        """
        wireshark display filter expression,to reduce pcap file
        """
        return self._wsFilter

    @rFilter.setter
    def rFilter(self,expression):
        """
        display filter expression in wireshark syntax,to reduce pcap file
        :param expression:
        :type expression: str
        :return:
        """
        self._wsFilter = expression

    @property
    def fields(self):
        """
        requested fields list in wireshark syntax
        """
        return self._requestedFields

    @fields.setter
    def fields(self,fieldsList):
        """
        requested fields list in wireshark syntax
        :param fieldsList:
        :type fieldsList: list[str]
        """
        self._requestedFields.append(fieldsList)

    @property
    def result(self):
        """
        list filled by last run() with entries according to view parameters
        :return:
        """
        return self._result

    @property
    def index_filter(self):
        return self._index_filter

    @index_filter.setter
    def index_filter(self,expression):
        """
        Specify index filter by using expression like '>=2' or  or '==12' etc..
        :type expression: str
        """
        self._index_filter = "frame.number >= " + expression

    def _process_command(self, cmd, process_func):
        success = 0
        with open(self._outFile, "wb") as appOut:
            ack = subprocess.call(cmd, stdout=appOut)
        if ack == success:
            res = process_func()
        else:
            res = None
        return res

    def _build_fields_command(self):
        tsCMD = tsharkCommandBuilder()

        tsCMD.add_option(TSHARK_ENUMS.OPTIONS.IN_FILE, self.current_pcap_file)
        if not exists(self.current_pcap_file): #todo exception source file not exists
            self.current_pcap_file = self._current_pcap_file
        if self.rFilter:
            tsCMD.add_option(TSHARK_ENUMS.OPTIONS.DISPLAY_FILTER, self.rFilter)
        if self.index_filter:
            tsCMD.add_option(TSHARK_ENUMS.OPTIONS.DISPLAY_FILTER, self.index_filter)
        if self.fields:
            tsCMD.add_option(TSHARK_ENUMS.OPTIONS.OUT_FORMAT_OPTION, TSHARK_ENUMS.OUT_FORMAT_OPTIONS.FIELDS.value)
            fields_list = self.default_fields + self.fields
            for item in fields_list:
                tsCMD.add_option(TSHARK_ENUMS.OPTIONS.ADD_FIELD, item)
                tsCMD.add_option(TSHARK_ENUMS.OPTIONS.FIELD_PRINT_OPTION, TSHARK_ENUMS.FIELD_PRINT_OPTIONS.AGGREGATOR.value + self.delimeter)

        return tsCMD.build_command()

    def extract_raw_packet_data(self, frame_id):
        cmd = self._build_raw_data_command(frame_id)
        return self._process_command(cmd,self._proccess_raw_data_file)

    def _build_raw_data_command(self,index):
        tsCMD = tsharkCommandBuilder()
        tsCMD.add_option(TSHARK_ENUMS.OPTIONS.IN_FILE, self.current_pcap_file)
        tsCMD.add_option(TSHARK_ENUMS.OPTIONS.RAW_PACKET_DATA)
        tsCMD.add_option(TSHARK_ENUMS.OPTIONS.DISPLAY_FILTER, "frame.number == " + index)
        return tsCMD.build_command()

    def _process_fields_file(self):
        ans = []
        with open(self._outFile, "r") as tsharkOut:
            for line in tsharkOut.readlines():
                fieldsValues = line.split('\t')
                entry = packetFieldsResultEntry()
                entry._parent = self
                for i,field in enumerate(self.default_fields + self.fields):
                    result = (copy.copy(fieldsValues[i])).replace('\n',"")
                    result = self._process_multiple_results(result)
                    entry[field] = result
                ans.append(entry)
        return ans

    def _proccess_raw_data_file(self):
        ans = ''

        with open(self._outFile, "r") as tsharkOut:
            for line in tsharkOut.readlines():
                ans+=line
        return ans

    def _process_multiple_results(self, string):
        lst = string.split(self.delimeter)
        return lst if len(lst) else [string]

    def run(self):
        # type: () -> list[packetFieldsResultEntry]
        """
        Execute shark app and extract results according to filter and requested fields of the view
        :rtype: object
        :return:
        """
        cmd = self._build_fields_command()
        self._result = self._process_command(cmd, self._process_fields_file)
        return self._result

    def _reduce_pcap(self):
        if self.rFilter:
            self._pcap_file = "cap_"+self.name
            tsharkCall = [
                'shark.exe',
                '-r',
                self._parent._pcap_file,
                '-Y',
                self.rFilter,
                '-w',
                self._pcap_file
            ]
            subprocess.call(tsharkCall)