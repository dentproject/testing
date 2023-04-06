""" Logger module
"""
import logging
import logging.config
import os
from logging.handlers import TimedRotatingFileHandler

import yaml

from dent_os_testbed.constants import LOGDIR

app_logging_configured = False


def setup_logging(default_path='log_config.yaml', default_level=logging.INFO):
    """
    Setup logging module - Loads log configuration
    """
    path = default_path
    global app_logging_configured
    # "%(asctime)s - %(name)s - %(levelname)s - %(fileName)s - %(message)s"

    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                if not os.path.exists(LOGDIR):
                    os.makedirs(LOGDIR)
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
                app_logging_configured = True
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                app_logging_configured = True
    else:
        logging.basicConfig(level=default_level)
        app_logging_configured = True
        print('Failed to load configuration file. Using default configs')


class LoggerAdapter(logging.LoggerAdapter):
    """
    Adapter class used for customizing log format of the message
    """

    def process(self, msg, kwargs):
        """
        Process log message - Append tag to log message if available

        Args:
            msg: Log message
            kwargs: Keyword args of the log message
        """
        if 'tag' in self.extra:
            return '[%s] %s' % (self.extra['tag'], msg), kwargs
        return msg, kwargs


class TaggedLogger:
    """
    TaggedLogger - Log messages with a tag
    """

    def __init__(self, logger, tag):
        """
        Initializliation for class TaggedLogger:

        Args:
            logger(Logger.Apploger): Logger
            tag: Message to tag the log messages with
        """
        self.logger = logger
        self.tag = tag
        self.adapter = LoggerAdapter(logger, {'tag': tag})

    def info(self, *args):
        """
        Info log

        Args:
            args: Variable args representing the log message
        """
        self.adapter.info(*args)

    def debug(self, *args):
        """
        Debug log

        Args:
            args: Variable args representing the log message
        """
        self.adapter.debug(*args)

    def error(self, *args):
        """
        Error log

        Args:
            args: Variable args representing the log message
        """
        self.adapter.error(*args)

    def warning(self, *args):
        """
        Warning log

        Args:
            args: Variable args representing the log message
        """
        self.adapter.warn(*args)

    def exception(self, *args, **kw_args):
        """
        Exception log

        Args:
            args: Variable args representing the log message
        """
        self.adapter.exception(*args, **kw_args)

    def getChild(self, suffix):
        """
        Get a child for this logger

        Args:
            suffix (str): Suffix name space of the child logger

        Returns:
            Logger instance which is a child of this logger
        """
        return TaggedLogger(logger=self.logger.getChild(suffix), tag=self.tag)


class Logger:
    """
    Base class for Logger
    """

    def info(self, *args):
        """
        Info log

        Args:
            args: Variable args representing the log message
        """
        self.logger.info(*args)

    def debug(self, *args):
        """
        Debug log

        Args:
            args: Variable args representing the log message
        """
        self.logger.debug(*args)

    def error(self, *args):
        """
        Error log

        Args:
            args: Variable args representing the log message
        """
        self.logger.error(*args)

    def warning(self, *args):
        """
        Warning log

        Args:
            args: Variable args representing the log message
        """
        self.logger.warn(*args)

    def exception(self, *args, **kw_args):
        """
        Exception log

        Args:
            args: Variable args representing the log message
        """
        self.logger.exception(*args, **kw_args)

    def tag_logs(self, tag):
        """
        Tag this logger with a given tag

        Args:
            tag (str): Tag for the log messages

        Returns:
            TaggedLogger instance
        """
        return TaggedLogger(self.logger, tag)


class DeviceLogger(Logger):
    """
    Device specific logger
    """

    LOG_MSG_FMT = '%(asctime)s - %(name)s - %(levelname)s  - %(message)s'

    def __init__(self, device_name=None, log_file_name=None, logger=None):
        """
        Initializliation for class DeviceLogger:

        Args:
            device_name(str): Name of the device and
            log_file_name(str): Name of the log file or
            logger = logger

        Raises:
            ValueError: If arguments are invalid
        """
        if device_name and log_file_name:
            self.logger = logging.getLogger(device_name)
        elif logger:
            self.logger = logger
        else:
            raise ValueError(
                'Either logger instance or device_name' + 'log_filename should be passed'
            )
        self.logger.setLevel(logging.DEBUG)
        log_dir = f'./logs/{device_name}'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        handler = TimedRotatingFileHandler(
            log_dir + '/' + log_file_name, when='h', interval=1, backupCount=10
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(DeviceLogger.LOG_MSG_FMT))
        self.logger.addHandler(handler)

    def getChild(self, suffix):
        """
        Get a child for this logger

        Args:
            suffix (str): Suffix name space of the child logger

        Returns:
            Logger instance which is a child of this logger
        """
        return DeviceLogger(logger=self.logger.getChild(suffix))


class AppLogger(Logger):
    """
    Application logger
    """

    def __init__(self, name=None, logger=None):
        """
        Initializliation for class AppLogger:

        Args:
            name(str): Name of the logger (or)
            logger: logger instance

        Raises:
            ValueError: If arguments are invalid
            Exception: For generic failures
        """
        try:
            if not app_logging_configured:
                setup_logging()
            if logger:
                self.logger = logger
            elif name:
                self.logger = logging.getLogger(name)
            else:
                raise ValueError('Either logger instance or logger name should be passed')
        except Exception as e:
            print(str(e))
            raise e

    def getChild(self, suffix):
        """
        Get a child for this logger

        Args:
            suffix (str): Suffix name space of the child logger

        Returns:
            Logger instance which is a child of this logger
        """
        return AppLogger(logger=self.logger.getChild(suffix))
