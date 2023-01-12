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

"""
%%OpenSourceCode_License%%
%%License%% CC-Wiki
%%LicenseLink%% https://creativecommons.org/licenses/by-sa/3.0/
%%Authors%% https://stackoverflow.com/users/3856785/epi272314
%%CodeReference%% https://stackoverflow.com/questions/2953462/pinging-servers-in-python
%%AdaptedIn%% ping,ping_till_timeout
%%Description%%
Code adapted from Stack Overflow:
https://stackoverflow.com/
(Source: https://stackoverflow.com/questions/2953462/pinging-servers-in-python in Sep 2017)
Modified 2017
%%OpenSourceCode_License%%
"""



from platform import system as system_name # Returns the system/OS name
from os import system as system_call       # Execute a shell command

import time

from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger
from PyInfraCommon.GlobalFunctions.Utils.Time import TimeoutInstance


def ping(host,count = 1):
    """
    :param host: ip address of host
    :param count: number of ping requests to send
    :returns: Returns True if host (str) responds to a ping request
    :rtype: bool
    ** Remember that some hosts may not respond to a ping request even if the host name is valid.
    """
    # TODO: validate IP address is valid

    # Ping parameters as function of OS
    funcname = GetFunctionName(ping)
    parameters = "-n {}".format(count) if system_name().lower() == "windows" else "-c {}".format(count)
    # Pinging
    return system_call("ping " + parameters + " " + host) == 0


def ping_till_timeout(host,timeout,initial_delay=0.0):
    """
    pings the host till first reply or till timeout occurs
    :param host: ip address of host
    :param timeout: timeout in seconds to wait before giving up
    :param initial_delay: initial delay in seconds before starting the polling process
    :return: True if host replied or False otherwise
    :rtype :bool
    """
    TimeOut = TimeoutInstance()
    if initial_delay:
        time.sleep(initial_delay)
    res = True
    TimeOut.set(timeout)
    while not ping(host):
        if TimeOut.expired():
            res = False
            break
    return res



# our Code
def poll_socket_till_timeout(host,tcp_port,timeout):
    """
    polls a TCP socket till timeout occurs
    :param host: ip address of remote host
    :type host:str
    :param tcp_port: the tcp port number
    :type tcp_port:int
    :param timeout:timeout value in seconds
    :type timeout:int
    :return:True on success
    :rtype:bool
    """
    funcname = "poll_socket_till_timeout"
    import socket
    from PyInfraCommon.GlobalFunctions.Utils.Time import TimeOut
    res = True
    socket_opened = False
    TimeOut = TimeoutInstance()
    TimeOut.set(timeout)
    try:
        while not socket_opened and not TimeOut.expired():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                #socket_opened = (0 == s.connect_ex((host, tcp_port)))
                s.connect((host,int(tcp_port)))
                s.shutdown(socket.SHUT_RD)
                s.close()
                socket_opened = True
            except socket.error as ex:
                socket_opened = False
            except OSError:
                socket_opened = False
            except Exception as ex:
                socket_opened = False
                GlobalLogger.logger.warning(funcname + " received unexpected exception {}".format(ex.__class__.__name__))

    finally:
        return socket_opened