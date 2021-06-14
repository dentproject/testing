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


from collections import OrderedDict

from UnifiedTG.Unified.TGEnums import TGEnums
from UnifiedTG.Unified.Port import Port
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyImport import FilterPallette
from UnifiedTG.IxNetworkRestPy.IxNetworkRestPyImport import Capture


from UnifiedTG.Unified.Utils import Converter


class ixnRestpyPort(Port):
    _sentinel = object()  # used for _update_field function

    def __init__(self,port_uri=None, port_name=None):
        super(self.__class__, self).__init__(port_uri, port_name)
        self._IxExPortStats_dict = OrderedDict()


    def start_capture(self, rx=True, tx=False, limit=None, mode=None, bpf_filter=None):
        captureControlPlane = True
        captureDataPlane = True
        # Get the packet capturing vport
        vport = self._port_driver_obj
        vport.RxMode = 'captureAndMeasure'
        # -softwareEnabled == Control Plane
        # -hardwareEnabled == Data Plane
        port_capture = vport.Capture  # type: Capture
        port_capture.SoftwareEnabled = captureControlPlane
        port_capture.HardwareEnabled = captureDataPlane
        port_capture.Start()

    def stop_capture(self, cap_file_name="", cap_mode="buffer"):
        self.vport.Capture.Stop()
        #ixNetwork.info('Total data packets captured: {}'.format(vport.Capture.DataPacketCounter))
        # There could be thousands of packets captured.  State the amount of packets to
        # inspect with a starting value and an ending value.
        packetsCount = self.vport.Capture.DataPacketCounter
        temp_buff_list = []
        for packetNumber in range(0, packetsCount):
            try:
                # Note: GetPacketFromDataCapture() will create the packet header fields
                self.vport.Capture.CurrentPacket.GetPacketFromDataCapture(Arg2=packetNumber)
                #packetHeaderStacks = vport.Capture.CurrentPacket.Stack.find()
                hex = self.vport.Capture.CurrentPacket.PacketHex.split()
                [hex.pop(0) for idx in range(2)]
                hex = ' '.join(hex)
                temp_buff_list.append(hex)
            except Exception as errMsg:
                print('\nError: {}'.format(errMsg))
                continue
        self.capture_buffer = temp_buff_list
        super(self.__class__, self).stop_capture()
            # for packetHeader in packetHeaderStacks.find():
            #     print('\nPacketHeaderName: {}'.format(packetHeader.DisplayName))
            #     for field in packetHeader.Field.find():
            #         print('\t{}: {}'.format(field.DisplayName, field.FieldValue))

                    # Do your parsing and logics here using the packetHeader and field.FieldValue

    def _read_speed(self):
        speedInt = self._port_driver_obj.ActualSpeed
        self.properties._speed = TGEnums._converter.speed_to_SPEED(speedInt)

    def apply_filters(self):

        def handle_filter_conditions(trigger, current_stat_prefix):
            # type: (trafficFilter, object) -> object
            patternCount = 0
            udpate_list = {}
            for cond in trigger.conditions:
                if cond.match_term._type is TGEnums.MATCH_TERM_TYPE.MAC_DA:
                    dest_field = 'CaptureFilterDA'
                    value = 'notAddr' if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 'addr'
                elif cond.match_term._type is TGEnums.MATCH_TERM_TYPE.MAC_SA:
                    dest_field = 'CaptureFilterSA'
                    value = 'notAddr' if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 'addr'
                elif cond.match_term._type is TGEnums.MATCH_TERM_TYPE.CUSTOM:
                    dest_field = 'CaptureFilterPattern'
                    if patternCount > 0:
                        value = "pattern1AndPattern2"
                    else:
                        value = 'notPattern' if cond.logical_operator is TGEnums.LOGICAL_OPERATOR.NOT else 'pattern'
                    patternCount += 1
                elif cond.match_term._type is TGEnums.MATCH_TERM_TYPE.SIZE:
                    from_size = 'CaptureFilterFrameSizeFrom'
                    to_size = 'CaptureFilterFrameSizeTo'
                    size_enable = 'CaptureFilterFrameSizeEnable'
                    udpate_list[size_enable] = True
                    udpate_list[from_size] = cond.match_term._from_size
                    udpate_list[to_size] = cond.match_term._to_size
                    continue
                if patternCount < 2 or cond.match_term._type is not TGEnums.MATCH_TERM_TYPE.CUSTOM:
                    value += str(cond.match_term._id)

                udpate_list[dest_field] = value

            filter_obj.update(**udpate_list)
                #field = 'filter.' + current_stat_prefix + dest_field
                #self._update_field(driver_field=field, value=value)

        # caller_name = inspect.stack()[1][3]
        # need_write = False if caller_name is "apply" else True
        terms = list(set().union(self.filter_properties.filters[1]._get_match_term_list(),
                                 self.filter_properties.filters[2]._get_match_term_list(),
                                 self.filter_properties.filters[3]._get_match_term_list(),
                                 self.filter_properties.capture_filter._get_match_term_list()
                                 )
                     )

        udpate_list = {}
        ixiaResourceMap = {'SA': 0, 'DA': 0, 'Pattern': 0}
        for term in terms:
            patternValue = term._pattern if term._type is not TGEnums.MATCH_TERM_TYPE.SIZE else None
            patternValue = patternValue.replace('{','').replace('}','')
            if term._type is TGEnums.MATCH_TERM_TYPE.MAC_DA:
                dest_field = 'DA'
            elif term._type is TGEnums.MATCH_TERM_TYPE.MAC_SA:
                dest_field = 'SA'
            elif term._type is TGEnums.MATCH_TERM_TYPE.CUSTOM:
                dest_field = 'Pattern'
                patId = ixiaResourceMap[dest_field] + 1
                udpate_list['PatternOffset' + str(patId)] = term._offset
                #self._update_field(driver_field='filterPallette.patternOffset' + str(patId), value=term._offset)
                spacedPattern = ""
                copyPattern = Converter.remove_non_hexa_sumbols(term._pattern[:])
                while copyPattern:
                    spacedPattern += copyPattern[:2]
                    spacedPattern += " "
                    copyPattern = copyPattern[2:]
                patternValue = spacedPattern
            elif term._type is TGEnums.MATCH_TERM_TYPE.SIZE:
                continue
            ixiaResourceMap[dest_field] += 1
            term._id = ixiaResourceMap[dest_field]
            field = dest_field + str(ixiaResourceMap[dest_field])
            udpate_list[field] = patternValue
            mask = dest_field + 'Mask' + str(ixiaResourceMap[dest_field])
            if term._mask is not None:
                mask_val = term._mask
            else:
                pat = Converter.remove_non_hexa_sumbols(patternValue)
                mask_len = len(pat) / 2 - 1
                mask_val = "00"
                for i in range(int(mask_len)):
                    mask_val += " 00"
            udpate_list[mask] = mask_val

        # fp_obj.Pattern1 = 'AA'
        # fp_obj.DA1 = '00 11 22 33 44 55'
        if udpate_list:
            #cap_obj = self._port_driver_obj.Capture  # type: Capture
            fp_obj = self._port_driver_obj.Capture.FilterPallette  # type: FilterPallette
            fp_obj.update(**udpate_list)

        triggers = list(filter(lambda x: x is not None, self.filter_properties.filters))
        triggers.append(self.filter_properties.capture_filter)
        #self._port_driver_obj.filter.ix_set_default()
        for trId, trigger in enumerate(triggers):
            trId += 1
            if trId < 3:
                continue
                current_stat_prefix = 'userDefinedStat' + str(trId)
            elif trId == 4:
                current_stat_prefix = 'captureFilter'
                filter_obj = self._port_driver_obj.Capture.Filter  # type: Filter
                filter_obj.CaptureFilterEnable = int(trigger.enabled)
            elif trId == 3:
                continue
                current_stat_prefix = 'captureTrigger'
            #filter_obj.CaptureFilterEnable = int(trigger.enabled)
            if not trigger.enabled:
                continue
            handle_filter_conditions(trigger, current_stat_prefix)
