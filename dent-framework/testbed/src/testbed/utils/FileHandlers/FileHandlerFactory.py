"""Factory implementation for getting FileHandler instance
"""
from testbed.utils.FileHandlers.LocalFileHandler import LocalFileHandler


class FileHandlerTypes:
    """Types of file handlers"""

    LOCAL = 0
    S3 = 1


class FileHandlerFactory(object):
    """Factory class to get FileHandler instance"""

    def __init__(self):
        """Initializer"""
        pass

    @staticmethod
    def get_file_handler(file_type, logger):
        """Get FileHanlder instance based on type

        Args:
            file_type - Type of file handler
            logger (Logger.Apploger): Logger

        Returns:
            FileHandler instance

        Raises:
            NotImplementedError - For unsupported types
            ValueError - For invalid file_type
        """
        if file_type == FileHandlerTypes.LOCAL:
            return LocalFileHandler(logger)
        elif file_type == FileHandlerTypes.S3:
            raise NotImplementedError
        else:
            raise ValueError("Unknown file type: %s" % file_type)
