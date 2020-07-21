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
# from exceptions import *


class CoSException(Exception):
    """\
    CoSException : inherent Exception
    define all CommService Exception that may occur in CommServices code
    """
    def __init__(self, message, errors=None):
        super(CoSException, self).__init__(message)
        self.errors = errors


class PythonComException(Exception):
    """\
    PythonComException : inherent Exception
    define general Exception that may occur in python communication code
    """
    def __init__(self, message, errors=None):
        super(PythonComException, self).__init__(message)
        self.errors = errors


class BaseCommException(Exception):
    """\
    BaseCommException : inherent Exception
    define all Base Communication Layer Exception that may occur in serial/telnet
    base layer code
    """
    def __init__(self, message, errors=None):
        super(BaseCommException, self).__init__(message)
        self.errors = errors


class ConnectionFailedException(BaseCommException):
    """
    Will be raised when the reconnect is failed
    """

    def __init__(self, connection_name, msg, e=None, errors=None):
        strerr = e.strerror if hasattr(e, 'strerror') and e.strerror is not None else ""
        message = e.message if hasattr(e, 'message') and e.message is not None else ""
        err = "exception message : " + message + strerr if e is not None else ""
        super(ConnectionFailedException, self).__init__(connection_name + " Connection Failed!!, " + msg + err)
        self.errors = errors


class DisconnectFailedException(BaseCommException):
    """
    Will be raised when the reconnect is failed
    """

    def __init__(self, connection_name, e, errors=None):
        strerr = e.strerror if hasattr(e, 'strerror') and e.strerror is not None else ""
        message = e.message if hasattr(e, 'message') and e.message is not None else ""
        err = "exception message : " + message + strerr if e is not None else ""
        super(DisconnectFailedException, self).__init__(connection_name + " Disconnection Failed!!, " + err)

        self.errors = errors


class ReconnectionFailedException(BaseCommException):
    """
    Will be raised when the reconnect is failed
    """

    def __init__(self, connection_name, e, errors=None):
        strerr = e.strerror if hasattr(e, 'strerror') and e.strerror is not None else ""
        message = e.message if hasattr(e, 'message') and e.message is not None else ""
        err = "exception message : " + message + strerr if e is not None else ""
        super(ReconnectionFailedException, self).__init__(connection_name + " Reconnection Failed!!, " + err)

        self.errors = errors


class WriteFailedException(BaseCommException):
    """
    Will be raised when the write is failed
    """

    def __init__(self, connection_name, e, errors=None):
        strerr = e.strerror if hasattr(e, 'strerror') and e.strerror is not None else ""
        message = e.message if hasattr(e, 'message') and e.message is not None else ""
        err = "exception message : " + message + strerr if e is not None else ""
        super(WriteFailedException, self).__init__(connection_name + " Write Failed!!, " + err)

        self.errors = errors


class ReadFailedException(BaseCommException):
    """
    Will be raised when the read is failed
    """

    def __init__(self, connection_name, e, errors=None):
        strerr = e.strerror if hasattr(e, 'strerror') and e.strerror is not None else ""
        message = e.message if hasattr(e, 'message') and e.message is not None else ""
        err = "exception message : " + message + strerr if e is not None else ""
        super(ReadFailedException, self).__init__(connection_name + " Read Failed!!, " + err)

        self.errors = errors


class ConnectionLostException(BaseCommException):
    """
    Will be raised when the connection is lost
    """

    def __init__(self, connection_name, errors=None):
        super(ConnectionLostException, self).__init__(connection_name + " Connection Lost")
        self.errors = errors
