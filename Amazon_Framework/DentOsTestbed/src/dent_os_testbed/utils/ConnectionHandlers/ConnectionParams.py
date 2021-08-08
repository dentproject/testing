"""Module defining the connection params used for SSH and serial connections
"""


class ConnectionParams:
    """
    Class representing the connection params used for SSH and serial connections
    """

    def __init__(self, builder):
        """
        ConnectionParams Initializliation

        Args:
            builder (ConnectionParams.Builder): Builder object
        """
        self.username = builder._username
        self.password = builder._password
        self.ip = builder._ip
        self.public_key = builder._public_key
        self.baudrate = builder._baudrate
        self.dev = builder._serial_dev
        self.hostname = builder._hostname
        self.logger = builder._logger
        self.log_file_path = builder._log_file_path
        self.pssh = builder._pssh
        self.aws_region = builder._aws_region
        self.store_domain = builder._store_domain
        self.store_type = builder._store_type
        self.store_id = builder._store_id


class Builder:
    """
    Class used for building the ConnectionParams
    """

    def __init__(self):
        """
        ConnectionParams.Builder Initializliation
        """
        self._username = ""
        self._ip = ""
        self._hostname = ""
        self._password = ""
        self._public_key = ""
        self._baudrate = -1
        self._serial_dev = ""
        self._logger = None
        self._log_file_path = ""
        self._pssh = False
        self._aws_region = ""
        self._store_domain = ""
        self._store_type = ""
        self._store_id = ""

    def username(self, username):
        """
        Set username for this ConnectionParams.Builder

        Args:
            username(str): Username
        """
        self._username = username
        return self

    def ip(self, ip):
        """
        Set ip for this ConnectionParams.Builder

        Args:
            ip(str): IP address
        """
        self._ip = ip
        return self

    def hostname(self, hostname):
        """
        Set hostname for this ConnectionParams.Builder

        Args:
            hostname(str): Host name
        """
        self._hostname = hostname
        return self

    def password(self, password):
        """
        Set password for this ConnectionParams.Builder

        Args:
            password(str):Password
        """
        self._password = password
        return self

    def public_key(self, public_key):
        """
        Set public key (used in SSH connections) for this ConnectionParams.Builder

        Args:
            public_key(str): Public key to use for SSH connections
        """
        self._public_key = public_key
        return self

    def baudrate(self, baudrate):
        """
        Set baudrate (used in serial connections) for this ConnectionParams.Builder

        Args:
            baudrate(str): Baudrate to use for serial connections
        """
        self._baudrate = baudrate
        return self

    def serial_dev(self, serial_dev):
        """
        Set serial device (used in serial connections) for this ConnectionParams.Builder

        Args:
            serial_dev(str): Serial device
        """
        self._serial_dev = serial_dev
        return self

    def logger(self, logger):
        """
        Set logger for this ConnectionParams.Builder.

        Args:
            logger(Logger.Apploger): Logger to use for logs associated with the connection.
        """
        self._logger = logger
        return self

    def log_file_path(self, log_file_path):
        """
        Set log_file_path for this ConnectionParams.Builder.

        Args:
            logger(str): Log file to use for logs associated with the connection.
        """
        self._log_file_path = log_file_path
        return self

    def pssh(self, pssh):
        """
        Set pssh for this ConnectionParams.Builder.

        Args:
            logger(str): Log file to use for logs associated with the connection.
        """
        self._pssh = pssh
        return self

    def aws_region(self, aws_region):
        """
        Set aws_region for this ConnectionParams.Builder.

        Args:
            logger(str): Log file to use for logs associated with the connection.
        """
        self._aws_region = aws_region
        return self

    def store_domain(self, store_domain):
        """
        Set store_domain for this ConnectionParams.Builder.

        Args:
            logger(str): Log file to use for logs associated with the connection.
        """
        self._store_domain = store_domain
        return self

    def store_type(self, store_type):
        """
        Set store_type for this ConnectionParams.Builder.

        Args:
            logger(str): Log file to use for logs associated with the connection.
        """
        self._store_type = store_type
        return self

    def store_id(self, store_id):
        """
        Set store_id for this ConnectionParams.Builder.

        Args:
            logger(str): Log file to use for logs associated with the connection.
        """
        self._store_id = store_id
        return self

    def build(self):
        """
        Build ConnectionParams with the attributes of this class.
        """
        return ConnectionParams(self)
