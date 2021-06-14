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

from Tests.Implementations.VLAN.GenericVlanFlow import VlanFlow
from Tests.Implementations.VLAN.TaggedAPI import PriorityAPI, QInQAPI, TaggedSizeAPI, \
    TaggedBroadcastMulticastAPI, TaggedUnicastAPI, TrunkModeMultiBroadCastAPI, TrunkModeUnicastAPI


class TaggedBroadcastFlow(VlanFlow):

    def __init__(self, testName=None):
        super(TaggedBroadcastFlow, self).__init__(testName)
        self.APIs = TaggedBroadcastMulticastAPI(self)


class TaggedMulticastFlow(VlanFlow):

    def __init__(self, testName=None):
        TaggedMulticastAPI = type('TaggedMulticastAPI', (TaggedBroadcastMulticastAPI,),
                                  {'setupStream': lambda self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00',
                                                         dstMac='ff:ff:ff:ff:ff:ff':
                                  TaggedBroadcastMulticastAPI.setupStream(self, tgDutLinks, srcMac=srcMac,
                                                                          dstMac='01:00:00:00:00:11')})
        super(TaggedMulticastFlow, self).__init__(testName)
        self.APIs = TaggedMulticastAPI(self)


class TaggedUnicastFlow(VlanFlow):

    def __init__(self, testName=None):
        # these lines must exist in every test !
        super(TaggedUnicastFlow, self).__init__(testName)
        self.APIs = TaggedUnicastAPI(self)


class TrunkModeBroadcastFlow(VlanFlow):

    def __init__(self, testName=None):
        super(TrunkModeBroadcastFlow, self).__init__(testName)
        self.APIs = TrunkModeMultiBroadCastAPI(self)


class TrunkModeMulticastFlow(VlanFlow):

    def __init__(self, testName=None):
        TrunkModeMulticastAPI = type('TaggedMulticastAPI', (TrunkModeMultiBroadCastAPI,),
                                     {'setupStream': lambda self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00',
                                                            dstMac='ff:ff:ff:ff:ff:ff':
                                     super(TrunkModeMulticastAPI, self).setupStream(tgDutLinks,
                                                                                    dstMac='01:00:00:00:00:11')})
        super(TrunkModeMulticastFlow, self).__init__(testName)
        self.APIs = TrunkModeMulticastAPI(self)


class TrunkModeUnicastFlow(VlanFlow):

    def __init__(self, testName=None):
        super(TrunkModeUnicastFlow, self).__init__(testName)
        self.APIs = TrunkModeUnicastAPI(self)


class PriorityFlow(VlanFlow):

    def __init__(self, testName=None):
        super(PriorityFlow, self).__init__(testName)
        self.APIs = PriorityAPI(self)
        self.TestSteps.Step[7] += " and add random priority to tagged packets"
        self.TestSteps.Step[9] += "\nVerify that the priority was not stripped from the packet"


class QInQFlow(VlanFlow):

    def __init__(self, testName=None):
        # these lines must exist in every test !
        super(QInQFlow, self).__init__(testName)
        self.APIs = QInQAPI(self)
        self.TestSteps.Step[7] += " and add random ctags to tagged packets"
        self.TestSteps.Step[9] += "\nVerify that the ctag was not stripped from the packet"


class TaggedSizeFlow(VlanFlow):

    def __init__(self, testName=None):
        super(TaggedSizeFlow, self).__init__(testName)
        self.TestSteps.Step[9] += "\nVerify that the tagged packet size is bigger in 4 bytes than untagged packet"
        self.APIs = TaggedSizeAPI(self)
