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

from multiprocessing import freeze_support

from PyInfraCommon.GlobalFunctions.ASYNC.Multiprocessing import ProcessWorker,ProcessController


def func(i):
    print("running {}".format(i))

def test_ProcessWorker():
    processes  =[]
    for i in range(5):
        p = ProcessWorker(name="func",target=func,i=i)
        p.start()
        processes.append(p)

    for i,p in enumerate(processes):
        print (i)
        p.join()
pass

def test_ProcessController():
    p = ProcessController()
    for i in range(5):
        p.add_worker(target=func,name="func_{}".format(i,i=i),i=i)

    p.run_all()

if __name__ == '__main__':
    freeze_support()
    #test_ProcessWorker()
    test_ProcessController()
    pass