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

from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyImport import StatViewAssistant


class ixNetworkRestPyStats(object):
    def __init__(self,parent_ixnetwork):
        self._ixnetwork = parent_ixnetwork
        self._port_statistics = None  # type: StatViewAssistant
        self._flow_statistics = None  # type: StatViewAssistant
        self._macsec_statistics = None  # type: StatViewAssistant

    @property
    def port(self):
        if not self._port_statistics:
            self._port_statistics = StatViewAssistant(self._ixnetwork, 'Port Statistics',
                                                      Timeout=5)  # type: StatViewAssistant
        return self._port_statistics

    @property
    def macsec(self):
        if not self._macsec_statistics:
            self._macsec_statistics = StatViewAssistant(self._ixnetwork, 'Static MACsec Per Port',
                                                        Timeout=20)  # type: StatViewAssistant
        return self._macsec_statistics


    def print_port_stats(self):
        for rowNumber, Stat in enumerate(self.port.Rows):
            self._ixnetwork.info('\n\nSTATS: {}\n\n'.format(Stat))
            self._ixnetwork.info('\nRow:{}  Stat Name:{}  Port Name:{} \n'.format(
                rowNumber, Stat['Stat Name'], Stat['Port Name']))


    def print_flow_stats(self):
        for rowNumber, flowStat in enumerate(self._flow_statistics.Rows):
            self._ixnetwork.info('\n\nSTATS: {}\n\n'.format(flowStat))
            self._ixnetwork.info('\nRow:{}  TxPort:{}  RxPort:{}  TxFrames:{}  RxFrames:{}\n'.format(
                rowNumber, flowStat['Tx Port'], flowStat['Rx Port'],
                flowStat['Tx Frames'], flowStat['Rx Frames']))