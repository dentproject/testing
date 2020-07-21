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


class PathException(Exception):
    """
    PathException : inherent Exception, indicate that path of script is invalid
    """
    def __init__(self, message, errors=None):
        super(PathException, self).__init__(message)
        self.errors = errors

class WrongTypesException(Exception):
    """
    WrongTypesException : inherent Exception
    defines a case when the parameter sent to a method is of a wrong type
    """
    def __init__(self, message, errors=None):
        super(WrongTypesException, self).__init__(message)
        self.errors = errors

class ScriptInnerException(Exception):
    """
    ScriptInnerException : inherent Exception
    defines a case when raised exception from the script itself
    """
    def __init__(self, message, errors=None):
        super(ScriptInnerException, self).__init__(message)
        self.errors = errors

class ProcessIDException(Exception):
    """
    ScriptInnerException : PID Exception
    defines a case when the user provide invalid PID
    """
    def __init__(self, message, errors=None):
        super(ProcessIDException, self).__init__(message)
        self.errors = errors
