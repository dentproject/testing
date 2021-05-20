"""Module - Base class implmentation of File I/O handling
"""


class FileHandler(object):
    """
    Base class for file I/O handling. APIs are implemented by the derived classes
    """

    def read(self, filename):
        """
        Read from given filename

        Args:
            filename(str): Filename (full path) from which the contents has to be read

        Returns:
            Contents of the file as string

        Raises:
            Exception - For generic failures

        """
        raise NotImplementedError

    def write(self, filename, data):
        """
        Write data to the given file

        Args:
            filename(str): Filename (full path) to which the contents has to be written

        Raises:
            Exception - For generic failures
        """
        raise NotImplementedError

    def delete(self, filename):
        """
        Delete the given file

        Args:
            filename(str): Filename (full path) to which has to be deleted

        Raises:
            Exception - For generic failures
        """
        raise NotImplementedError

    def mkdir(self, path):
        """
        Create directory

        Args:
            path(str) - Path of the directory

        Raises:
            Exception - For generic failures
        """
        raise NotImplementedError

    def copy(self, src, dst, follow_symlinks=True):
        """
        Copy

        Args:
            src(str) - Source of copy
            dst(str) - Destination of copy
            follow_symnlinks - If false, src and dst both refer to symbolic links.

        Raises:
            Exception - For generic failures
        """
        raise NotImplementedError
