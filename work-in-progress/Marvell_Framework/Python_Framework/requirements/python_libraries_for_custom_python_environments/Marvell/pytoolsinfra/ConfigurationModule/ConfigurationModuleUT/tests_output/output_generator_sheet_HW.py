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

class DUTGeneralInfo(object):
    def __init__(self):
        self.device_name = []
        self.dut_corner = []
        self.lot_number = []
        self.xml_file = []


class Portdata(object):
    def __init__(self):
        self.port_number = []
        self.destination_port = []
        self.port_mode = []
        self.port_speed = []
        self.port_clock_source = []
        self.port_ppm = []
        self.port_training = []
        self.adaptive_serdes_tune = []
        self.port_fec = []
        self.tx_amp = []
        self.tx_emph_0 = []
        self.tx_emph_1 = []
        self.pve_source = []
        self.pve_destination = []
        self.start_serdes = []
        self.stop_serdes = []
        self.port_interconnect = []


class BoardGeneralInfo(object):
    def __init__(self):
        self.board_name = []
        self.board_revision = []
        self.board_id = []


class SystemConfig(object):
    def __init__(self):
        self.sw_revision = []
        self.uboot_revsion = []
        self.cpss_revision = []
        self.hws_revision = []
        self.main_eeprom_revision = []
        self.em_eeprom_revision = []


class SystemInitalization(object):
    def __init__(self):
        self.serdes_init = []
        self.appdemo_name = []
        self.run_appdemo = []
        self.run_cliexit = []
        self.appdemo_db_entry_name = []
        self.appdemo_db_entry_value = []
        self.preinit_string = []
        self.cpssinit_board_id = []
        self.cpssinit_board_rev = []
        self.cpssinit_reload_eeprom = []
        self.tftp_server_ip = []
        self.tftp_dir = []
        self.galtisfilename = []
        self.port_configuartion_method = []


class CommonTestCharacterization(object):
    def __init__(self):
        self.dut_core_frequency = []
        self.cpu_frequency = []
        self.sdram_frequency = []
        self.cpu = []
        self.pp_interrupt = []
        self.test_character = []
        self.traffic_type = []
        self.cpu_ramp_up_delay = []
        self.board_on_off_polarity = []
        self.number_of_repetitions = []


class PrintOptions(object):
    def __init__(self):
        self.print_debug = []
        self.print_tg_counters = []
        self.print_port_status = []
        self.print_egress_ingress_counters = []
        self.print_mib_counters = []
        self.print_events = []
        self.print_serdes_parameters = []
        self.print_bc3_rs_fec_counters = []


class DebugOptions(object):
    def __init__(self):
        self.ddr3_interface_test = []
        self.internal_memories_bist = []
        self.mem_bist_pattern = []
        self.prbs_pattern = []
        self.loopback_options = []
        self.training_results_display = []


class TGPorts(object):
    def __init__(self):
        self.ports_quantity = []


class TGConfigPort(object):
    def __init__(self):
        self.portnum = []
        self.tg_port_destination = []
        self.tg_type = []
        self.packets_pattern = []
        self.da = []
        self.sa = []
        self.transmit_mode = []
        self.burst_count = []
        self.multiburst_count = []
        self.inter_burst_gap = []
        self.inter_burst_gap_scale = []
        self.rx_trigger_for_da = []
        self.rx_trigger_for_sa = []
        self.rx_trigger_for_sa_p1 = []
        self.fec = []


class EMConfig(object):
    def __init__(self):
        self.paltier_available = []
        self.flextc_available = []
        self.flextc_ip = []
        self.oven_available = []
        self.com_for_oven = []
        self.em_available = []
        self.em_interface_class = []
        self.actionaftertempchange = []
        self.actionaftervoltagechange = []


class TempCycleTestCharacterization(object):
    def __init__(self):
        self.temp_cycles_range = []
        self.soak_time = []
        self.ramp_time = []
        self.temp_wait = []
        self.tesen_treshold = []


class NonTempCycleTestCharacterization(object):
    def __init__(self):
        self.dut_temp_case = []


class VoltageCorners(object):
    def __init__(self):
        self.span_all_vt_combinations = []
        self.number_of_smm = []
        self.reset_after_avs_config = []
        self.a2d_ch_num = []
        self.vcore_avs = []
        self.smm0_ch0 = []
        self.smm0_ch0_name = []
        self.smm0_ch1 = []
        self.smm0_ch1_name = []
        self.smm1_ch0 = []
        self.smm1_ch0_name = []
        self.smm1_ch1 = []
        self.smm1_ch1_name = []


class SingleTesttime(object):
    def __init__(self):
        self.test_time = []


class PortConfiguration(object):
    def __init__(self):
        self.number_of_groups = []
        self.ports_per_group = []


class setup(object):
    def __init__(self):
        self.dut_general_info = DUTGeneralInfo()
        self.port_data1 = Portdata()
        self.board_general_info = BoardGeneralInfo()
        self.system_config = SystemConfig()
        self.system_initalization = SystemInitalization()
        self.common_test_characterization = CommonTestCharacterization()
        self.print_options = PrintOptions()
        self.debug_options = DebugOptions()
        self.tg_ports = TGPorts()
        self.tg_config_port = TGConfigPort()
        self.em_config = EMConfig()
        self.temp_cycle_test_characterization = TempCycleTestCharacterization()
        self.non_temp_cycle_test_characterization = NonTempCycleTestCharacterization()
        self.voltage_corners = VoltageCorners()
        self.single_testtime = SingleTesttime()
        self.port_configuration = PortConfiguration()
        self.port_data2 = Portdata()
        self.port_data3 = Portdata()
        self.port_data4 = Portdata()
        self.port_data5 = Portdata()
        self.port_data6 = Portdata()
        self.port_data7 = Portdata()
        self.port_data8 = Portdata()


