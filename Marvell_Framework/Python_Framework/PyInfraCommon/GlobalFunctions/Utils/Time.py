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

from __future__ import absolute_import
from builtins import str
from builtins import object
from datetime import datetime
from time import time

class StopWatch(object):
    """
    util class to measure time
    """
    _start_time = None
    _end_time = None
    _format = None
    @classmethod
    def start(cls,time_format=None):
        """

        :param format: if None: count in resolution of seconds float
        if not None: then stop() returns string of HH:MM:SS passing time
        :return:
        """
        cls._format = time_format
        cls._start_time = time() if time_format is None else datetime.now()

    @classmethod
    def stop(cls):
        cls._end_time = time() if cls._format is None else datetime.now()
        return str(cls._end_time- cls._start_time)

class StopWatchInstance(object):
    """
    util class to measure time
    """

    def __init__(self,time_format=None):
        self._start_time = None
        self._end_time = None
        self._format = time_format
        self.start(self._format)


    def start(self,time_format=None):
        """

        :param format: if None: count in resolution of seconds float
        if not None: then stop() returns string of HH:MM:SS passing time
        :return:
        """
        self._format = time_format
        self._start_time = time() if time_format is None else datetime.now()

    def stop(self):
        self._end_time = time() if self._format is None else datetime.now()
        return str(self._end_time- self._start_time)


class TimeOut(object):
    """
    util class that implement timeout mechanism
    """
    _start_time = None
    _end_time = None
    _timeout = None
    
    @classmethod
    def set(cls,timout_val):
        """
        starts measuring elpassed time from this point
        :param timout_val: timeout value in seconds
        :type timout_val: float
        :return:
        :rtype:
        """
        cls._timeout = timout_val
        cls._start_time = time()
    
    @classmethod
    def expired(cls):
        """
        checks if elpassed time since set has passed already
        :return:  True if time has already passed (timeout), False otherwise
        :rtype: bool
        """
        return time() - cls._start_time >= cls._timeout


class TimeoutInstance(object):
    """
    util class that implement timeout mechanism 
    """
    
    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._timeout = None

    def set(self, timout_val):
        """
        starts measuring elpassed time from this point
        :param timout_val: timeout value in seconds
        :type timout_val: float
        :return:
        :rtype:
        """
        self._timeout = timout_val
        self._start_time = time()

    def expired(self):
        """
        checks if elpassed time since set has passed already
        :return:  True if time has already passed (timeout), False otherwise
        :rtype: bool
        """
        return time() - self._start_time >= self._timeout
    