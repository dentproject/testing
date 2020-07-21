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

import threading
from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException


class ThreadManager(object):
    """"
    helper class to run multiple threads workers
    """

    class ThreadWorker(threading.Thread):
        """
        helper class to execute tasks in a thread
        """

        def __init__(self, target, name=None,daemon =True, *args, **kwargs):
            threading.Thread.__init__(self, name=name)
            self.__target = target
            self.__args = args
            self.__kwargs = kwargs
            self.Error = threading.Event()
            self.exception_info = ""
            self.daemon = daemon  # we use daemon threads to ensue it will get kill upon main thread exit
            self.__has_started = False
            self.result = None

        @property
        def started(self):
            return self.__has_started
        @started.setter
        def started(self,val):
            self.__has_started = True

        def run(self):
            try:
                self.started = True
                self.result = self.__target(*self.__args, **self.__kwargs)
            except Exception as ex:
                self.Error.set()
                self.exception_info = GetStackTraceOnException(ex)

    def __init__(self):
        self.workers = set()  # type: set[ThreadManager.ThreadWorker]
        self.Done = threading.Event()
        self.Error = threading.Event()
        self.errors = ""

    def add_worker(self,target,name=None,*args,**kwargs):
        w = self.ThreadWorker(target=target,name=name,*args,**kwargs)
        self.workers.add(w)

    def clear_workers(self):
        self.workers = set()

    def run_all(self,blocking=True):
        """
        run all workers
        :param blocking: if True will wait till all workers finished
        :return:
        :rtype:
        """
        for w in self.workers:
            if not w.started:
                w.start()
        if blocking:
            self.wait_all_done()

    def wait_all_done(self):
        """
        wait till all workers finished and collect errors from them
        :return:
        :rtype:
        """
        running_workers = list(self.workers)
        while running_workers:
            finished_workers_ids = []
            for w_id,w in enumerate(list(running_workers)):
                if not w.is_alive():
                    if w.Error.is_set() or w.result == False:
                        self.Error.set()
                        self.errors += w.exception_info
                    finished_workers_ids.append(w_id)
            # remove the finished workers
            for i in finished_workers_ids:
                running_workers.pop(i)
        self.clear_workers()
        self.Done.set()

































