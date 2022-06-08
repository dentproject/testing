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

import random
from CLI_GlobalFunctions.SwitchDev.Bridge.Bridge1QConfig import Bridge1QConfig
from Tests.Implementations.VLAN.GenericVlanAPI import GenericVlanAPI, GenericVlanUnicastAPI, \
    GenericVlanBroadMultiCastAPI


def toHex(val):
    try:
        return hex(val)[2:]
    except TypeError:
        return toHex(int(val))


class TaggedAPI:

    def __init__(self):
        self._txInterfaces = {}
        self._rxInterfaces = {}

    """ finals """
    STAG_DEF_OFF = 14
    CTAG_DEF_OFF = 18

    def addTriggers(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', mask=None):
        for txPort, txDits in self._txInterfaces.items():
            for vlanTested in txDits['vlan_tested']:
                try:
                    for rxPort in self._rxInterfaces[vlanTested]:
                        rxDutPort = tgDutLinks[rxPort].DutDevPort.name
                        isTagged = Bridge1QConfig.isTagged(rxDutPort, str(vlanTested))
                        if isTagged and not len(
                                [x for x in Bridge1QConfig.getVIDs(rxDutPort).values() if x != 'tagged']):
                            self._addVlanTagging(tgDutLinks[rxPort], toHex(vlanTested), txPort=tgDutLinks[int(txPort)])
                except KeyError as e:
                    if e.args[0] in txDits['vlan_tested'] or e.args[0] == 'X':
                        continue
                    raise KeyError

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):

        for txPort, txDits in self._txInterfaces.items():
            for vlanTested in txDits['vlan_tested']:
                stream = self._GET_PACKET_BY_ID(tgDutLinks[int(txPort)], vlanTested)
                if stream:
                    stream.add_vlan('VID#{}'.format(vlanTested))
                    stream.vlans['VID#{}'.format(vlanTested)].vid.value = vlanTested
                    stream.size = 68

    """""""""""""""""""""""""""""""""" PROTECTED FUNCTIONS """""""""""""""""""""""""""""""""""""""

    def _addVlanTagging(self, rxPort, vlanTested, vlanMask=None, txPort=None, tag=STAG_DEF_OFF):
        mask = '00' + vlanMask if len(vlanTested) > 2 and vlanMask else vlanMask
        offset = tag if len(vlanTested) > 2 else tag + 1
        vlanTested = (4 - len(vlanTested)) * '0' + vlanTested if len(vlanTested) > 2 else vlanTested
        termVID = rxPort.TGPort.filter_properties.create_match_term(vlanTested, offset, mask=mask)
        rxPort.TGPort.filter_properties.capture_filter.add_condition(termVID)

    """""""""""""""""""""""""""""""""" PROTECTED FINAL FUNCTIONS """""""""""""""""""""""""""""""""""""""

    def _GET_PACKET_BY_ID(self, txPort, vlanTested):
        if f'testPacketVID#{vlanTested}' in txPort.TGPort.streams:
            return txPort.TGPort.streams[f'testPacketVID#{vlanTested}'].packet

    def _LAST_VLAN_ADDED(self, txPort, vlanTested):
        if f'testPacketVID#{vlanTested}' in txPort.TGPort.streams:
            lastVlan = txPort.TGPort.streams[f'testPacketVID#{vlanTested}']
            return list(lastVlan.packet.vlans.values())[-1]


########################################################################################################################


class TaggedBroadcastMulticastAPI(GenericVlanBroadMultiCastAPI, TaggedAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        GenericVlanBroadMultiCastAPI.setupStream(self, tgDutLinks, srcMac, dstMac)
        TaggedAPI.setupStream(self, tgDutLinks, srcMac, dstMac)

    def addTriggers(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', mask=None):
        GenericVlanBroadMultiCastAPI.addTriggers(self, tgDutLinks, srcMac, mask)
        TaggedAPI.addTriggers(self, tgDutLinks, srcMac, mask)


########################################################################################################################


class TaggedUnicastAPI(GenericVlanUnicastAPI, TaggedAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        # set packet for learning
        GenericVlanUnicastAPI.setupStream(self, tgDutLinks, srcMac, dstMac)
        TaggedAPI.setupStream(self, tgDutLinks, srcMac, dstMac)

    def addTriggers(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', mask=None):
        GenericVlanUnicastAPI.addTriggers(self, tgDutLinks, srcMac, mask)
        TaggedAPI.addTriggers(self, tgDutLinks, srcMac, mask)

########################################################################################################################


class TrunkModeMultiBroadCastAPI(GenericVlanBroadMultiCastAPI, TaggedAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        # set packet for learning
        GenericVlanBroadMultiCastAPI.setupStream(self, tgDutLinks, srcMac, dstMac)
        TaggedAPI.setupStream(self, tgDutLinks, srcMac, dstMac)

    def addTriggers(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', mask=None):
        super(TrunkModeMultiBroadCastAPI, self).addTriggers(tgDutLinks, srcMac, mask)
        for rxPort in list(self._rxInterfaces.values())[-1]:
            vlanTested = list(self._rxInterfaces.keys())[-1]
            GenericVlanAPI._addTriggers(tgDutLinks[rxPort].TGPort, srcMac, mask)
            isTagged = Bridge1QConfig.isTagged(tgDutLinks[rxPort].DutDevPort.name, str(vlanTested))
            if isTagged:
                self._addVlanTagging(tgDutLinks[rxPort], toHex(vlanTested), vlanMask='0F')


########################################################################################################################


class TrunkModeUnicastAPI(GenericVlanUnicastAPI, TaggedAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        # set packet for learning
        GenericVlanUnicastAPI.setupStream(self, tgDutLinks, srcMac, dstMac)
        TaggedAPI.setupStream(self, tgDutLinks, srcMac, dstMac)

    def addTriggers(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', mask=None):
        super(TrunkModeUnicastAPI, self).addTriggers(tgDutLinks, srcMac, mask)
        vlanTested = list(self._rxInterfaces.keys())[-1]
        GenericVlanAPI._addTriggers(tgDutLinks[self._rxInterfaces[vlanTested][-1]].TGPort, srcMac, srcMask=mask)
        isTagged = Bridge1QConfig.isTagged(tgDutLinks[self._rxInterfaces[vlanTested][-1]].DutDevPort, str(vlanTested))
        if isTagged:
            self._addVlanTagging(tgDutLinks[self._rxInterfaces[vlanTested][-1]], toHex(vlanTested), vlanMask='0F')

        for port in self._nonRxPorts:
            GenericVlanAPI._addTriggers(port.TGPort, srcMac, '00 00 00 00 00 FF')


########################################################################################################################


class PriorityAPI(TaggedBroadcastMulticastAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        GenericVlanBroadMultiCastAPI.setupStream(self, tgDutLinks, srcMac, dstMac)
        TaggedAPI.setupStream(self, tgDutLinks, srcMac, dstMac)

        for txPort, txDits in list(self._txInterfaces.items()):
            for vlanTested in txDits['vlan_tested']:
                priority = random.randint(0, 7)
                self._LAST_VLAN_ADDED(tgDutLinks[int(txPort)], vlanTested).priority = priority

    """""""""""""""""""""""""""""""""" PROTECTED FUNCTIONS """""""""""""""""""""""""""""""""""""""

    def _addVlanTagging(self, rxPort, vlanTested, vlanMask=None, txPort=None, tag=TaggedAPI.STAG_DEF_OFF):
        priority = self._LAST_VLAN_ADDED(txPort, int(vlanTested)).priority
        priorityAndVlan = f"{toHex(priority * 2)}{(3 - len(vlanTested)) * '0'}{vlanTested}"
        super(PriorityAPI, self)._addVlanTagging(rxPort, priorityAndVlan)


########################################################################################################################


class QInQAPI(TaggedBroadcastMulticastAPI):

    def setupStream(self, tgDutLinks, srcMac='AA:AA:AA:AA:AA:00', dstMac='ff:ff:ff:ff:ff:ff'):
        super(QInQAPI, self).setupStream(tgDutLinks, srcMac, dstMac)
        for txPort, txDits in self._txInterfaces.items():
            for vlanTested in txDits['vlan_tested']:
                ctag = random.randint(1, Bridge1QConfig.MAX_VLANS)
                lastStream = self._GET_PACKET_BY_ID(tgDutLinks[int(txPort)], vlanTested)
                lastStream.add_vlan("ctag")
                lastStream.vlans['ctag'].vid.value = ctag

    """""""""""""""""""""""""""""""""" PROTECTED FUNCTIONS """""""""""""""""""""""""""""""""""""""

    def _addVlanTagging(self, rxPort, vlanTested, vlanMask=None, txPort=None, tag=TaggedAPI.STAG_DEF_OFF):
        super(QInQAPI, self)._addVlanTagging(rxPort, vlanTested, vlanMask, tag)
        ctag = toHex(self._LAST_VLAN_ADDED(txPort, int(vlanTested)).vid.value)
        super(QInQAPI, self)._addVlanTagging(rxPort, (4 - len(ctag)) * '0' + ctag, tag=TaggedAPI.CTAG_DEF_OFF)


########################################################################################################################


class TaggedSizeAPI(TaggedBroadcastMulticastAPI):

    def _addVlanTagging(self, rxPort, vlanTested, vlanMask=None, txPort=None, tag=TaggedAPI.STAG_DEF_OFF):
        super(TaggedSizeAPI, self)._addVlanTagging(rxPort, vlanTested, vlanMask, tag)
        size = self._GET_PACKET_BY_ID(txPort, 'X').size
        termVID = rxPort.TGPort.filter_properties.create_size_match_term(from_size=size + 4, to_size=size + 1000)
        rxPort.TGPort.filter_properties.capture_filter.add_condition(termVID)
