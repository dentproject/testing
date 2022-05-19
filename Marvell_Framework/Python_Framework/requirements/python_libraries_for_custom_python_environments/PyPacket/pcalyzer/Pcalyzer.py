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

import shutil
import tempfile
import atexit
import subprocess
from enum import Enum
import re
import os
import types

from PyPacket.pcalyzer.Pcaview import pcaview
from PyPacket.pcalyzer.Common import myItems
from PyPacket.pcalyzer.shark.Text2pcapComamander import tex2PcapCommandBuilder,create_text2pcap_input_format


class pcalyzer(object):


    class INPUT_FORMAT(Enum):
        PCAP_FILE = 0
        HEXA_STRING = 1

    _hex_string_pattern = re.compile('^(?:[A-Fa-f\d]{2}\s?:?)+$')
    _tmp_dir = tempfile.mkdtemp(prefix ='PyPacket_')

    def __init__(self, input_data, work_dir=None):
        """
        create analyzer object
        :param input_data: pcap file path or packet hex string(00 FF 01 ... )
        :param work_dir: specify directory for output files,if not - users temp dir
        """
        self._work_dir = work_dir if work_dir else self.__class__._tmp_dir
        self._pcap_file = self.__class__._unify_input_data(input_data,self._work_dir)
        self._pcaviews = myItems() #type: list[pcaview]
        self.results = []
        self._default_view_name = "default_view"

    @property
    def input_data(self):
        return self._pcap_file

    @input_data.setter
    def input_data(self,input_data):
        self._pcap_file = self.__class__._unify_input_data(input_data,self._work_dir)

    def init_default_view(self, filter , fields):
        if self._default_view_name not in self.views:
            self.add_view(filter,fields,self._default_view_name)

    @property
    def default_view(self):
        if self._default_view_name in self.views:
            return self.views[self._default_view_name]

    @classmethod
    def _detect_input_format(cls, input_data):
        if input_data:
            if cls._hex_string_pattern.match(input_data):
                return cls.INPUT_FORMAT.HEXA_STRING
            return cls.INPUT_FORMAT.PCAP_FILE

    @classmethod
    def _unify_input_data(cls,input_data,work_dir):
        if not input_data:
            return None
        isList = isinstance(input_data, types.ListType)
        simpleEntry = input_data[0] if isList else input_data
        input_format = cls._detect_input_format(simpleEntry)
        if input_format is pcalyzer.INPUT_FORMAT.PCAP_FILE:
            return input_data
        elif input_format is pcalyzer.INPUT_FORMAT.HEXA_STRING:
            if not isList:
                input_data = [input_data]
            return cls.hex2pcap(input_data,"hex2pcap",work_dir)
        else:
            return None #todo exception unknown input format

    @classmethod
    def single_request(cls, input_data,fields = None, filter = None):
        input_data = cls._unify_input_data(input_data,cls._tmp_dir)
        tmpView = pcaview(name="tmp_view", filter=filter, fields=fields, workDir=cls._tmp_dir)
        tmpView._pcap_file = input_data
        return tmpView.run()

    @classmethod
    def _cleanup(cls):
        shutil.rmtree(cls._tmp_dir)

    @classmethod
    def hex2pcap(cls, hex_packets, name, dest_dir = None):
        dest_dir = dest_dir if dest_dir else cls._tmp_dir
        infile = cls._process_hex_packets(hex_packets, name, dest_dir)
        outFile = dest_dir+os.sep+name+".pcapng"
        x = tex2PcapCommandBuilder()
        x.add_option(None, infile)
        x.add_option(None, outFile)
        # print("x is: {}".format(str(x)))
        cmd = x.build_command()
        # print("cmd is: {}".format(str(cmd)))
        res = subprocess.call(cmd)
        return outFile

    @classmethod
    def _process_hex_packets(cls, hex_packets, name, dest_dir):
        hex_packet_path = dest_dir+os.sep+ name+".txt"
        out = ""
        for hex_packet in hex_packets:
            out += create_text2pcap_input_format(hex_packet) + "\n"
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        with open(hex_packet_path, 'wb') as the_file:
            the_file.write(out)
        return hex_packet_path

    def add_view(self, filter= None, fields = [], name=None):
        """
        Create specific view to analyze pcap file,all input parameters use wireshark syntax
        :param filter: display filter expression
        :param fields: requested fields list ["eth.src","eth.dst"]
        :param name: optional,if None - generated, view name to access by
        :return:
        """
        name = name if name else "View_"+str(self._pcaviews.count)
        obj = pcaview(name, filter, fields, pcalyzer._tmp_dir)
        obj._parent = self
        self._pcaviews[name] = obj
        return name

    @property
    def views(self):
        # type: () -> list[pcaview]
        return self._pcaviews

    def run(self):
        for v in self._pcaviews:
            self._pcaviews[v].run()


atexit.register(pcalyzer._cleanup)