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

from openpyxl.compat.singleton import Singleton


class Executer:

    def __init__(self, channel=None):
        """
        :param channel: The channel where the commands will be executed
        """
        self.channel = channel if channel else None

    def __getattr__(self, name):
        return lambda *args, timing=False, **kwargs: \
            "{}".format('/usr/bin/time -f \"%e\" ' if timing else '') + \
            ' '.join(name.split('_') + list('%s %s' % (k, v) for k, v in kwargs.items() if v is not None) + list(
                filter(None, map(str, args))))

    def execute(self, commandOrCommands=None, timeout=10.0):
        """
        Execute commandsOrCommands if not None
        :param commandOrCommands: The command or commands to run; if not specified, execute self._config
        :param timeout: timeout in seconds the amount of time to wait till prompt appears
        :return: any output from the channel except the prompt if commandOrCommands is not None; None otherwise
        """
        self.channel.GetBuffer(timeOutSeconds=0.1)
        if commandOrCommands:
            self.channel.SendCommandAndWaitForPattern(commandOrCommands, ExpectedPrompt=self.channel.shellPrompt, timeOutSeconds=timeout)
            return self.channel.lastBufferTillPrompt.replace('\r', '').replace(self.channel.shellPrompt.pattern[:-2], '')

    def execAsFile(self, configOrCmds=None, *args, timeout=600000, getReturnCode=False):
        """
        Execute the command as a bash file
        :return: error message, if exists
        """
        returnCode = None
        from io import BytesIO
        with self.channel.SSHClient.open_sftp() as ftp:
            # creates an output file and an error file with name out<hash> and err<hash> to minimize the issues in critical section
            # (when using NFS image load)
            import random
            randTrail = random.getrandbits(128)
            fileName = f'config{randTrail}.sh'
            ftp.putfo(BytesIO(configOrCmds.encode()), fileName)
            err = self.execute(f'chmod 755 {fileName} && ./{fileName} {" ".join(map(str, args))}', timeout=timeout)
            if getReturnCode:
                returnCode = self.echo('"${?}"')
            self.execute(f'rm -f {fileName}')
        if not getReturnCode:
            return err
        else:
            return err, returnCode


class Getter(Executer):
    """
    Getter is a subclass of Executer; the purpose of this class is to retrieve information from channel in real-time
    """

    def __init__(self, channel=None):
        """
        :param channel: The channel where the commands will be executed
        """
        super(Getter, self).__init__(channel)

    def __getattr__(self, item):
        def _(*args, timing=False, timeout=10.0, **kwargs):
            """
            :param args: command's args
            :param timing: True to measure the command execution time; False otherwise
            :param timeout: timeout in seconds the amount of time to wait till prompt appears
            :param kwargs: command's kwargs
            :return: the string representation of the command
            """
            command = self.execute(super(Getter, self).__getattr__(item)(*args, timing=timing, **kwargs),
                                   timeout=timeout)
            if timing:
                command = command.split('\n', 1)
                return float(command[0]), command[1] if len(command) == 2 else None
            return command

        return lambda *args, timing=False, timeout=10.0, **kwargs: _(*args, timing=timing, timeout=timeout, **kwargs)

    def execute(self, commandOrCommands=None, timeout=10.0):
        """
        Execute commandsOrCommands if not None
        :param commandOrCommands: The command or commands to run; if not specified, execute self._config
        :param timeout: timeout in seconds the amount of time to wait till prompt appears
        :return: any output received while running the command/s
        """
        res = None
        if commandOrCommands:
            res = super(Getter, self).execute(commandOrCommands, timeout).strip(commandOrCommands).strip('\n')
        return res if res else None

    def getCmdOutputAsFile(self, cmd):
        """
        Execute the command and write its output to an output bash file, and then read the output file into a string.
        This function was made for very large output, which cannot be read using the simple socket read function.
        :return: a tuple of (output of the command, error message if exists or None otherwise)
        """
        with self.channel.SSHClient.open_sftp() as ftp:
            # creates an output file and an error file with name out<hash> and err<hash> to minimize the issues in critical section
            # (when using NFS image load)
            import random
            randTrail = random.getrandbits(128)
            err = self.execute(f'{cmd} > out{randTrail}', timeout=600000)

            # for some reason, file is not always created, so try at least 3 attempts
            for maxAttempts in range(3):
                try:
                    outputFile = ftp.open(f'out{randTrail}')
                    output = ''
                    for line in outputFile:
                        output += line
                    break
                except FileNotFoundError:
                    pass
                finally:
                    self.execute(f'rm -f out{randTrail}')
            else:  # if there was no break through the for loop
                return None, 'output file not found!'
        return output, err


class Setter(Executer):
    """
    Setter is a subclass of Executer; the purpose of this class is to send a bulk of configuration commands
    (as opposed to Getter, which sends each command immediately)
    """

    def __init__(self, channel=None):
        """
        :param channel: The channel where the commands will be executed
        """
        super(Setter, self).__init__(channel)
        self._config = ""

    def __getattr__(self, item):
        def _(command):
            self._config += f'{command}\n'

        return lambda *args, timing=False, **kwargs: _(
            super(Setter, self).__getattr__(item)(*args, timing=timing, **kwargs))

    def execute(self, commandOrCommands=None, timeout=10.0):
        """
        Execute commandsOrCommands if not None, else execute self._config
        :param commandOrCommands: The command or commands to run; if not specified, execute self._config
        :param timeout: timeout in seconds the amount of time to wait till prompt appears
        :return: any output received while running the command/s
        """
        temp = commandOrCommands
        if not commandOrCommands:
            commandOrCommands = self._config
        if commandOrCommands:
            res = '\n'.join(set(super(Setter, self).execute(commandOrCommands, timeout).split('\n')) - set(
                commandOrCommands.split('\n')))
            if not temp: self._config = ''
            return res if res else None

    def execAsFile(self, configOrCmds=None, *args):
        err = super(Setter, self).execAsFile(configOrCmds=self._config, *args)
        self._config = ''
        return err


class GlobalGetterSetter(metaclass=Singleton):

    def __init__(self):
        # setter is public because if chose to work with immediate execution of "set" commands,
        # it should be possible to set setter to getter
        self.setter = Setter()
        self._getter = Getter()
        self.setterOtherDut = Setter()
        self._getterOtherDut = Getter()
        self.setterSecondaryDut = Setter()
        self._getterSecondaryDut = Getter()

    # global getter shouldn't be changeable
    @property
    def getter(self):
        return self._getter

    @property
    def channel(self):
        return self._getter.channel

    # global getter shouldn't be changeable
    @property
    def getterOtherDut(self):
        return self._getterOtherDut

    @property
    def otherDutChannel(self):
        return self._getterOtherDut.channel

    @property
    def secondaryDutChannel(self):
        return self._getterSecondaryDut.channel

    @channel.setter
    def channel(self, channel):
        self.setter.channel = self._getter.channel = channel

    @otherDutChannel.setter
    def otherDutChannel(self, channel):
        self.setterOtherDut.channel = self._getterOtherDut.channel = channel

    @secondaryDutChannel.setter
    def secondaryDutChannel(self, channel):
        self.setterSecondaryDut.channel = self._getterSecondaryDut.channel = channel
