from dent_os_testbed.lib.poe_tester.dni.poe_serial_handler import PoeSerialHandler


class PoeTesterClient:
    def __init__(self, hostname, serial_dev, baudrate):
        self.handler = PoeSerialHandler(hostname, serial_dev, baudrate)
        self.menu_state = self.handler.get_current_menu()
        # Options for various menus found in DNI Poe Tester
        self.pair_types_dict = {
            'ATAF Auto': '0',
            'AP': '1',
            'AN': '2',
            'BN': '3',
            'BP': '4',
            'UPOE Auto': '5',
            'APBP': '6',
            'APBN': '7',
            'ANBP': '8',
            'ANBN': '9',
        }
        self.connection_option_dict = {
            'connect': 'C',
            'dis-connect': 'D',
        }
        self.lldp_options_dict = {
            'load level': {'field_input': 'S', 'field_prompt': r'Enter load level>\s*'},
            'classification': {'field_input': 'C', 'field_prompt': r'Enter Classification>\s*'},
            'Pair Status': {'field_input': '4', 'field_prompt': r'\(\w/\w\)>\s*'},
            'Power Pair': {'field_input': 'P', 'field_prompt': r'\(\d~\d\)>\s*'},
            'LLDP Status': {'field_input': 'L', 'field_prompt': r'\(\w/\w\)>\s*'},
            'CDP Status': {'field_input': 'D', 'field_prompt': r'\(\w/\w\)>\s*'},
            'Priority level': {'field_input': 'r', 'field_prompt': r'\(\w/\w/\w\)>\s*'},
        }
        self.toggle_dict = {
            'Enable': 'E',
            'Disable': 'D',
        }
        self.priority_dict = {'Critical': 'C', 'High': 'H', 'Low': 'L'}

    def get_general_info(self):
        self.handler.return_to_main_menu()
        general_info = self.handler.send_cmd_and_expect('G', r'Press any key to continue\s*')
        return general_info

    def get_status(self):
        self.handler.return_to_main_menu()
        status_info = self.handler.send_cmd_and_expect('S', r'Command>\s*')
        self.handler.send_cmd_and_expect('Q', r'Command>\s*')
        return status_info

    def parse_status(self):
        stats_dict = {}
        stats = list(filter(None, self.get_status()))
        title_index = stats.index(
            next((s for s in stats if s[0:2] == '<<' and s[-2:] == '>>'), None)
        )
        end_index = stats.index(next((s for s in stats if '<COMMAND>' in s), None))
        for line in stats[title_index + 1: end_index]:
            if '=' in line:
                continue
            tokens = line.split()
            if tokens[0] == 'Port':
                stats_dict = dict.fromkeys(list(map(int, tokens[1:])), None)
                stats_dict = {int(key): {} for key in tokens[1:]}
            else:
                category, values = line.split(':')
                category = category[: category.index('(') if '(' in category else None].strip()
                for index, value in enumerate(values.split()):
                    stats_dict[index + 1][category] = value
        return stats_dict

    def _set_port_config(self, port, field_input, field_prompt, field_data):
        """
        Helper function for configuring settings on port(s)
        Assumes the tester is already in a proper menu
        port: port number to configure
        field_input: Character that selects the intended option
        field_prompt: regex string that matches expected prompt string
        field_data: Value to put the setting at
        """
        self.handler.send_cmd_and_expect(field_input, r'changed>\s*')
        self.handler.send_cmd_and_expect(f'{port}\r\n', field_prompt)
        self.handler.send_cmd_and_expect(f'{field_data}', r'Command>\s*')

    def set_power_pair_config(self, input_data):
        port = input_data['port']
        power_pair_type = input_data['power pair type']
        self.handler.return_to_main_menu()
        self.handler.send_cmd_and_expect('P', r'Command>\s*')
        self._set_port_config(
            port, 'S', r'\(\d~\d\)>\s*', f'{self.pair_types_dict[power_pair_type]}'
        )
        self.handler.send_cmd_and_expect('A', r'Command>\s*')

    def set_loading_config(self, input_data):
        port = input_data['port']
        load_level = input_data['load level']
        self.handler.return_to_main_menu()
        self.handler.send_cmd_and_expect('L', r'Command>\s*')
        self._set_port_config(port, 'S', r'Enter load level>\s*', f'{load_level}\r\n')
        self.handler.send_cmd_and_expect('A', r'Command>\s*')

    def set_classification_config(self, input_data):
        port = input_data['port']
        classification = input_data['classification']
        self.handler.return_to_main_menu()
        self.handler.send_cmd_and_expect('C', r'Command>\s*')
        self._set_port_config(port, 'S', r'Enter Classification>\s*', f'{classification}\r\n')
        self.handler.send_cmd_and_expect('Q', r'Command>\s*')

    def set_test_connection(self, input_data):
        port = input_data['port']
        connection_option = input_data['connection option']
        self.handler.return_to_main_menu()
        self.handler.send_cmd_and_expect('D', r'Command>\s*')
        self._set_port_config(port, 'S', r'\(\w/\w\)>\s*', f'{connection_option[0]}')
        self.handler.send_cmd_and_expect('Q', r'Command>\s*')

    def set_lldp_options(self, input_data):
        port = input_data['port']
        lldp_option = self.lldp_options_dict[input_data['lldp_option']]
        value = input_data['value']
        value = self.toggle_dict.get(value, value)
        value = self.pair_types_dict.get(value, value)
        value = self.priority_dict.get(value, value)
        self.handler.return_to_main_menu()
        self.handler.send_cmd_and_expect('E', r'Command>\s*')
        self._set_port_config(
            port, lldp_option['field_input'], lldp_option['field_prompt'], f'{value}\r\n'
        )
        self.handler.send_cmd_and_expect('Q', r'Command>\s*')

    def reset_default(self, input_data):
        self.handler.return_to_main_menu()
        self.handler.send_cmd_and_expect('R', r'\(\w/\w\)>\s*')
        self.handler.send_cmd_and_expect(
            input_data['reset'][0], [r'Command>\s*', r'\w*\s\w*\s\w*\s\w*\s\w*\s*']
        )
        self.handler.send_cmd_and_expect('\r\n', r'Command>\s*')
