"""Module for local file I/O
"""
import os
import shutil

from testbed.utils.FileHandlers.FileHandler import FileHandler


class LocalFileHandler(FileHandler):
    """
    Implements APIs required for handling local files
    """

    def __init__(self, logger):
        """
        Initializliation for LocalFileHandler

        Args:
            logger (Logger.Apploger): Logger
        """
        self.applog = logger

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
        try:
            with open(filename, "r") as f:
                data = f.read()
                self.applog.debug("Read from file:%s" % data)
            return data
        except Exception as e:
            self.applog.exception("Error reading file:%s" % filename, exec_info=e)
            return None

    def write(self, filename, data):
        """
        Write data to the given file

        Args:
            filename(str): Filename (full path) to which the contents has to be written

        Raises:
            Exception - For generic failures
        """
        try:
            with open(filename, "w") as f:
                f.write(data)
                self.applog.debug("Wrote data:%s to to file:%s" % (filename, data))
        except Exception as e:
            self.applog.exception("Error writing file:%s" % filename, exec_info=e)
            raise

    def delete(self, filename):
        """
        Delete the given file

        Args:
            filename(str): Filename (full path) to which has to be deleted

        Raises:
            Exception - For generic failures
        """
        os.remove(filename)

    def mkdir(self, path):
        """
        Create directory

        Args:
            path(str) - Path of the directory

        Raises:
            Exception - For generic failures
        """
        if not os.path.exists(path):
            os.mkdir(path)

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
        src_path = src if os.path.isabs(src) else os.path.join(os.getcwd(), src)
        dst_path = dst if os.path.isabs(dst) else os.path.join(os.getcwd(), dst)
        try:
            shutil.copy2(src_path, dst_path, follow_symlinks=follow_symlinks)
            self.applog.info("Copy file succeeded src:%s dst:%s" % (src_path, dst_path))
        except:
            self.applog.error("Copy file failed src:%s dst:%s" % (src_path, dst_path))
            raise
