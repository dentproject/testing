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

from __future__ import print_function
from builtins import str
import os, inspect, sys, re, site, platform,pdb


def we_are_frozen():
    # All of the modules are built-in to the interpreter, e.g., by py2exe
    return hasattr(sys, "frozen")


def module_path():
    if we_are_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def GetMyRootPath():
    """
    searches in the __main__ module launched from commandline
    :param retDir: a prefix that your directory name should contain
    :return: the full path of the seachdir or None if not found
    """
    if hasattr(sys.modules['__main__'], "__file__"):
        rootdir = inspect.getabsfile(sys.modules['__main__'].__file__)
    else:
        rootdir = module_path()
    if rootdir is not None:
        rootdir = os.path.dirname(rootdir)
        tmp = os.path.abspath(os.path.join(rootdir, os.pardir))
        retDir = os.path.abspath(os.path.join(tmp, os.pardir))
        return  retDir
    else:
        print ("__main__ dont have __file__ attribute")
        return None


def SetMyRootPath(path):
    if path is not None:
        site.addsitedir(path)
