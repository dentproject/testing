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

import json5
from CLI_GlobalFunctions.SwitchDev.CLICommands.EntityConfig import GeneralEntityConfig
from CLI_GlobalFunctions.SwitchDev.CLICommands.Executer import GlobalGetterSetter


class ACLConfig(GeneralEntityConfig):

    LOWEST_PRIO = 49152

    @classmethod
    def addFilterSharedBlock(cls, block: int, parent=None, protocol=None, pref=None, handle=None, qdisq=None, skipSwOrHw='', **kwargs):
        """
        Create a new ACE in the ingress qdisc
        :param pref: specify the preference/priority of the rule within the qdisc
        :param skipSwOrHw: specify skip_sw/skip_hw selector (or nothing - default behavior)
        :param block: the shared block number id
        :param parent:
        :param protocol:
        :param handle:
        :param qdisq:
        :param kwargs: the flower selectors (e.g., src_ip=1.1.1.1, src_mac=00:00:00:00:00:01, etc.)
        :return:
        """
        assert skipSwOrHw in ('', 'skip_sw', 'skip_hw')
        return GlobalGetterSetter().setter.tc_filter_add(block=block, protocol=protocol, pref=pref,
                                                         parent=parent, handle=handle, qdisq=qdisq,
                                                         flower=skipSwOrHw + ' ' + ' '.join(
                                                             list("%s %s" % x for x in kwargs.items())))
    @classmethod
    def deleteTCFilterSharedBlock(cls, block, pref, handle=None):
        """
        delete the ACE from the shared block using the pref number
        :param pref: the preference number of the ACE
        :return: the error message from the board if received; None otherwise
        """
        return GlobalGetterSetter().setter.tc_filter_delete(block=block, pref=pref, handle=handle)

    def __init__(self, switchDevDutInterface, otherDut=False, executer=True):
        super(ACLConfig, self).__init__(switchDevDutInterface, otherDut, executer)
        self.__tcFilters = []
        self.__tcStats = []

    def getMatchedRule(self, pref, handle=None):
        """
        Returns a list of matched ACE with the same settings as provided in the arguments
        :param pref: the preference number of the requested ACE
        :return: a list of matched ACEs
        """
        if not self.__tcFilters:
            self.getTCFilters()
        if self.__tcFilters:
            for acl in filter(lambda x: 'options' in x, self.__tcFilters):
                if acl['pref'] == pref:
                    if not handle or handle == acl['handle']:
                        return acl

    def addQdisq(self, *args, **kwargs):
        """
        add an ingress qdisc to a port
        :param args:
        :param kwargs:
        :return: the error message from the board if received; None otherwise
        """
        return self._setter.tc_qdisc_add('ingress', dev=self, *args, **kwargs)

    def deleteQdisc(self, timeout=10):
        """
        delete the qdisc from the entity/port
        :return: the error message from the board if received; None otherwise
        """
        return self._setter.tc_qdisc_delete(f'dev {self} ingress', timeout=timeout)

    def addTCFilterFlower(self, parent=None, protocol=None, pref=None, handle=None, qdisq=None, skipSwOrHw='', **kwargs):
        """
        Create a new ACE in the ingress qdisc
        :param skipSwOrHw:
        :param parent:
        :param protocol:
        :param pref:
        :param handle:
        :param qdisq:
        :param kwargs:
        :return:
        """
        assert skipSwOrHw in ('', 'skip_sw', 'skip_hw')
        return self._setter.tc_filter_add(dev=f'{self} ingress', protocol=protocol, pref=pref,
                                          parent=parent, handle=handle, qdisq=qdisq,
                                          flower=skipSwOrHw + ' ' + ' '.join(list("%s %s" % x for x in kwargs.items())))

    def deleteTCFilterFlower(self, pref, handle=None):
        """
        delete the ACE from the entity/port using the pref number
        :param pref: the preference number of the ACE
        :return: the error message from the board if received; None otherwise
        """
        return self._setter.tc_filter_delete(dev=self, pref=pref, handle=handle, *['ingress'])

    def getTCFilters(self):
        """
        get the rules within the ingress qdisc of the port
        :return: a list of ACEs of the port's ingress qdisc
        """
        showFilters, err = self._getter.getCmdOutputAsFile(f'tc -j filter show dev {self} ingress')
        if not showFilters or err: return -1
        self.__tcFilters = json5.loads(showFilters)
        return self.__tcFilters

    def getTCStats(self):
        """
        Get the statistics of a port in json format (using "tc -s -j filter show" command)
        :return:
        """
        tcStats = self._getter.tc(f'-s -j filter show dev {self} ingress')
        self.__tcStats = json5.loads(tcStats)
        return self.__tcStats

    def getSpecificStats(self, pref, handle=1):
        """
        Get statistics of a specific rule by pref and handle
        :param pref: the preference of the rule
        :param handle:
        :return: a dict of {pref:{handle: <dict of stats of the rule}}
        """
        specificStats = {}
        for stat in filter(lambda x: 'options' in x, self.__tcStats):
            if stat.get('pref') == pref and stat['options'].get('handle') == handle:
                specificStats[pref] = {handle: stat['options']['actions'][0]['stats']}
        return specificStats
