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

import multiprocessing
import os
import subprocess
import sys
from multiprocessing import freeze_support

from collections import OrderedDict
from copy import copy, deepcopy
import time
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
import platform

_is_win = "windows" in platform.system().lower()
_is_linux = "linux" in platform.system().lower()

#https://stackoverflow.com/questions/1947904/how-can-i-pickle-a-nested-class-in-python
class _NestedClassGetter(object):
    """
    When called with the containing class as the first argument,
    and the name of the nested class as the second argument,
    returns an instance of the nested class.
    """
    def __call__(self, containing_class, class_name):
        nested_class = getattr(containing_class, class_name)

        # make an instance of a simple object (this one will do), for which we can change the
        # __class__ later on.
        nested_instance = _NestedClassGetter()

        # set the class of the instance, the __init__ will never be called on the class
        # but the original state will be set later on by pickle.
        nested_instance.__class__ = nested_class
        return nested_instance


class ProcessWorker(multiprocessing.Process):
    """
    helper class to execute functions in a child process
    """
    Queue_IPC = 0
    PIPE_IPC = 1

    def __init__(self, name, target, ipc=None,ipc_type=None,orphaned=False,child_init=None,daemon=True, *args, **kwargs):
        multiprocessing.Process.__init__(self,name=name)
        self._name = name
        self.__target = target
        self._orphaned = orphaned # set to True if you want to start a detached daemon process
        self._ipc_type = ipc_type
        self._exec_ipc = ipc  # used only for detecting exceptions on child process, type is expected to be
        self._child_init = child_init
        # multiprocessing.Queue | multiprocessing.Pipe
        self.__args = args
        self.__kwargs = kwargs
        self.exception_info = None
        # to assure all child process will terminate once main process terminates MUST be True unless orphaned process
        self.daemon = daemon if not orphaned else False
        self.daemon_popen = None  # daemon process handle for daemon processes
        # if orphaned:
        #     self.start = self.__start_daemon

    def _start_daemon(self):
        """
        overrides multiprocessing start for daemon process
        :return:
        :rtype:
        """
        python_exec = os.path.abspath(sys.executable)
        stderr= self.__kwargs.get("stderr",None)
        stdout = self.__kwargs.get("stdout",None)
        stdout_f = open(stdout,"w")
        stderr_f = stdout_f
        if stdout != stderr:
            stderr_f = open(stderr,"w")

        cmd = "{} {}".format(python_exec, self.__target)
        if _is_win:
            python_exec = os.path.join(os.path.dirname(python_exec),"pythonw.exe")
        if os.path.isfile(python_exec):
            cmd = "{} {}".format(python_exec,self.__target)

        self.daemon_popen = subprocess.Popen(cmd,creationflags=subprocess.CREATE_NEW_CONSOLE,close_fds=True,stdout=stdout_f,stderr=stderr_f)

    def run(self):
        try:
            if self._orphaned:
                # this should run on linux only
                if self._child_init is None:
                    # to avoid recursion loop
                    child_child = ProcessWorker(self._name, self._start_daemon, self._exec_ipc, self._ipc_type, orphaned=True, child_init=True, *self.__args, **self.__kwargs)
                    child_child.start()
                    time.sleep(0.005)
                    #self.terminate()
                else:
                    # child_child process code
                    self.__target()
            else:
                # normal child process
                self.__target(*self.__args, **self.__kwargs)
        except Exception as ex:
            self.exception_info = ex
            if self._exec_ipc:
                if self._ipc_type == self.Queue_IPC:
                    self._exec_ipc.put(GetStackTraceOnException(ex))
                elif self._ipc_type == self.PIPE_IPC:
                    self._exec_ipc.send(GetStackTraceOnException(ex))
                    self._exec_ipc.close()


class ProcessController(object):
    """"
    helper class to run multiple child process workers
    """


    class ProcessInfo(object):
        Queue_IPC = 0
        PIPE_IPC = 1

        def __init__(self,name="",pid=None,ipc_type=PIPE_IPC):
            self.ipc_type = ipc_type
            self.pipe_ends = None
            self.ipc = None
            if self.ipc_type == self.PIPE_IPC:
                parent_conn, child_conn = multiprocessing.Pipe()
                self.pipe_ends = (parent_conn,child_conn)
                self.ipc = parent_conn  # our end of the pipe
            else:
                self.ipc = multiprocessing.Queue()
            self.pid = pid
            self.name = name

        def __hash__(self):
            if self.pid is not None:
                return hash((self.name,self.pid))
            return hash(self.name)

        def __eq__(self, other):
            if self.pid is not None:
                return self.pid == other.pid and self.name == other.name
            return self.name == other.name

        def ipc_get(self):
            data = None
            try:
                if self.ipc:
                    if self.ipc_type == self.PIPE_IPC:
                        if self.ipc.poll():
                            data = self.ipc.recv()
                    else:
                        # type: multiprocessing.Queue
                        data = self.ipc.get()
            finally:
                return data



    def __init__(self):
        #TODO: make orderded dict work or replace with 2 lists for keys and values
        self.workers_info_pairs = [] # type: list[tuple[ProcessController.ProcessInfo,ProcessWorker]]
        self.Done = multiprocessing.Event()
        self.Error = multiprocessing.Event()
        self.errors = ""
        self.daemon_workers_info_pairs = [] # type: list[tuple[ProcessController.ProcessInfo,ProcessWorker]]
        freeze_support()

    def add_worker(self,target,name,*args,**kwargs):
        pinfo = self.ProcessInfo(name=name,ipc_type=self.ProcessInfo.PIPE_IPC)
        w = ProcessWorker(target=target,name=name,ipc=pinfo.pipe_ends[1],ipc_type=self.ProcessInfo.PIPE_IPC,*args,**kwargs)
        self.workers_info_pairs.append([pinfo,w])

    def add_daemon_worker(self, command, name, stderr,stdout,**kwargs):
        """
        ada a daemon worker - Note for cross-compatibility with windows and linux this must run in cli mode, hence target
         must be a program file name to run with optional args
        note that the args are cli args that would be parsed by target arg parser
        :param command:full path of the program name to run
        :type command:str
        :param name:name of the process
        :type name:str
        :param args:optional command line args to pass to target function file
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        if not all(os.path.isdir(os.path.dirname(p))for p in [stderr,stdout]):
            err = GetFunctionName(self.add_daemon_worke) +"one of the dirs in path of  stderr and or stdout dont exist, cant continue"
            raise Exception(err)
        pinfo = self.ProcessInfo(name=name,ipc_type=self.ProcessInfo.PIPE_IPC)
        w = ProcessWorker(target=command, name=name, ipc=pinfo.pipe_ends[1], ipc_type=self.ProcessInfo.PIPE_IPC, orphaned=True,stdout=stdout,stderr=stderr,**kwargs)
        self.daemon_workers_info_pairs.append([pinfo, w])


    def clear_workers(self):
        # warning this will not stop any running process
        del self.workers_info_pairs
        del self.daemon_workers_info_pairs
        self.workers_info_pairs = list()
        self.daemon_workers_info_pairs = list()

    def run_all(self,blocking=True):
        """
        run all workers
        :param blocking: if True will wait till all workers finished
        :return:
        :rtype:
        """
        for pair in self.workers_info_pairs:
            pinfo = pair[0]  #type: ProcessController.ProcessInfo
            w = pair[1]  # type:ProcessWorker
            w.start()
            time.sleep(0.001)
            pinfo.pid = w.pid

        for pair in self.daemon_workers_info_pairs:
            pinfo = pair[0]  #type: ProcessController.ProcessInfo
            w = pair[1]  # type:ProcessWorker
            w.start()
            time.sleep(0.001)
            pinfo.pid = w.pid

        if blocking:
            self.wait_all_done()

    def wait_all_done(self):
        """
        wait till all workers finished
        :return:
        :rtype:
        """
        running_workers_pinfo = [p[0] for p in self.workers_info_pairs]
        running_workers = [p[1] for p in self.workers_info_pairs]
        while running_workers:
            finished_workers_keys = []
            for i,w in enumerate(running_workers):  # type:ProcessWorker
                if not w.is_alive():
                    if running_workers_pinfo[i].ipc_get():
                        self.Error.set()
                        self.errors += running_workers_pinfo[i].name + GetStackTraceOnException(running_workers_pinfo[i].ipc_get()[0])
                    finished_workers_keys.append(i)
            # remove the finished workers
            for i in finished_workers_keys:
                running_workers.pop(i)

        self.Done.set()

    def kill_all(self):
        """
        kills all child processes
        :return:
        :rtype:
        """
        funcname = GetFunctionName(self.kill_all)
        for pair in self.workers_info_pairs:
            pinfo,w = pair[0],pair[1]
            if w.is_alive():
                try:
                    w.terminate()
                except Exception as ex:
                    print(funcname+ "failed to kill process {}: {}".format(pinfo.name,GetStackTraceOnException(ex)))

