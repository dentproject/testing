import re

import pexpect


class PoeSerialHandler:
    def __init__(self, hostname, serial_dev, baudrate):
        self.ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        self.generic_prompts = [
            '(?<!<)[A-Z]*[a-z]+>\s*',
            '\(\d~\d\)>\s*',
            '\(\w/\w\)>\s*',
            '\(\w/\w/\w\)>\s*',
            '.*\.\.\.',
        ]  # Add more generic input indicators
        self.child = pexpect.spawn(f'screen -S {hostname} {serial_dev} {baudrate}', maxread=4000)
        self.logfile = open('poe_tester_screen_log.txt', 'ab+')
        self.child.logfile = self.logfile
        for _ in range(10):
            self.child.send('\r\n')
        self.child.expect(self.generic_prompts)
        self.child.send('\r\n')
        self.child.send('\r\n')
        self.child.expect('Command>\s*')
        self.child.expect('Command>\s*')

    def check_connection(self):
        return self.child.isalive()

    def get_current_menu(self):
        self.child.send('\r\n')
        self.child.expect(self.generic_prompts)
        menu = self.child.before.decode('utf-8').splitlines()
        menu = list(map(lambda x: self.ansi_escape.sub('', x), menu))
        title = next((s for s in menu if s[0:2] == '<<' and s[-2:] == '>>'), None)
        return title

    def return_to_main_menu(self):
        self.child.send('\r\n')
        self.child.expect(self.generic_prompts)
        while self.get_current_menu() != '<< Main Menu >>':
            self.child.send('Q')
            self.child.expect('Command>\s*')
        return True

    def send_cmd_and_expect(self, cmd, expect='Command>\s*'):
        """Expectation is that the method starts off at a correct
        place on the command line, and also ends at a correct plane on the
        command line
        """
        self.child.send(cmd)
        self.child.expect(expect)
        data = self.child.before.decode('utf-8').splitlines()
        return list(map(lambda x: self.ansi_escape.sub('', x), data))

    def match_and_retrieve(self, pattern):
        self.child.send('\r\n')
        self.child.expect(pattern)
        data = self.child.match
        self.child.send('\r\n')
        self.child.expect(['Command>\s*', 'changed>\s*'])
        return self.ansi_escape.sub('', data.decode('utf-8'))

    def close(self):
        self.child.close()
