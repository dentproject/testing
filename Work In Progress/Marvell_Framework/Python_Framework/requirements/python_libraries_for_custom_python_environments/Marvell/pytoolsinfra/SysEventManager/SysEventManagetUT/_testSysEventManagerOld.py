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
from __future__ import absolute_import
from builtins import object
from Marvell.pytoolsinfra.SysEventManager.SysEventManager import *
from . import new_provider_events
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

class DataMsg(object):
    data1 = 'rrr'

d = DataMsg()
d.data1 = 'Test1'
e = threading.Event()

def listener1( data, topic=pub.AUTO_TOPIC):
    info = 'Method Listener.onTopic2 received "%s" message: %s'
    logging.debug(info % (topic.getName(), repr(data.data1)))
    e.set()


def sender1():
    e.clear()
    logging.debug('--- SENDING communication.connect async message ---')
    SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, d)
    event_is_set = e.wait(2)
    if event_is_set:
        logging.debug('---- SENT communication.connect async message ----')
    else:
        logging.error('---- No listener for communication.connect async message ----')

def sender1Sync():
    e.clear()
    logging.debug('--- SENDING communication.connect message ---')
    SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, d, sync=True)

    event_is_set = e.wait(2)
    if event_is_set:
        logging.debug('---- SENT communication.connect message ----')
    else:
        logging.error('---- No listener for communication.connect message ----')

def senderUnPreDefineMessage():
    try:
        logging.debug('--- SENDING UnPreDefineMessage message ---')
        SysEventManager.DispatchSysEvent('con.cof', d)
        logging.debug('---- SENT UnPreDefineMessage message ----')
    except Exception as e:
        logging.debug('---- SENT UnPreDefineMessage message and got exception: "{}" ----'.format(e))

def senderUnPreDefineMessageSync():
    # try:
        logging.debug('--- SENDING UnPreDefineMessageSync message ---')
        SysEventManager.DispatchSysEvent('con.cof', d, sync=True)
        logging.debug('---- SENT UnPreDefineMessageSync message ----')
    # except Exception as e:
        logging.debug('---- SENT UnPreDefineMessageSync message and got exception: \n"{}" ----'.format(e))

def onTopic1(msg, topic=pub.AUTO_TOPIC):
    info = 'Method Listener.onTopic1 received "%s" message: %s'
    print(info % (topic.getName(), repr(msg)))

def onNewTopic1(data, topic=pub.AUTO_TOPIC):
    info = 'Method Listener.onTopic1 received "%s" message: %s'
    print(info % (topic.getName(), repr(data)))


def run():
    logging.debug('**** Register to messages ****')
    SysEventManager.Register(EventNameEnum.COMM_CONNECT_EVENT, listener1)
    # SysEventManager.Register('con.cof', listener1)
    sender1()
    sender1Sync()

    logging.debug('\n**** Stop register to messages ****')
    SysEventManager.UnRegister(EventNameEnum.COMM_CONNECT_EVENT, listener1)
    sender1()
    sender1Sync()

    logging.debug('\n**** Check exceptions for not PreDefine Events ****')
    senderUnPreDefineMessage()
    senderUnPreDefineMessageSync()

    # SysEventManager.AddProviderClass(new_provider_events)
    # SysEventManager.Register('topic_1', onNewTopic1)
    # pub.sendMessage('topic_1', data='message for 1')

    # id = SysEventManager.Register(EventNameEnum.COMM_CONNECT_EVENT, listener1)
    # sender1()
    # SysEventManager.UnRegisterById(id)
    # sender1()

if __name__ == '__main__':

    # SysEventManager.Register('con.cof', listener1)
    run()
