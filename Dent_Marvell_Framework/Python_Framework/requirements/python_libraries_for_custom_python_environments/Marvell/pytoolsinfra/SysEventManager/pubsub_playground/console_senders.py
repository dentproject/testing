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
:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE.txt for details.
"""

from builtins import object
from pubsub import pub
from pubsub.py2and3 import print_


def doSomething1():
    print_('--- SENDING topic1.subtopic11 message ---')
    pub.sendMessage('topic1.subtopic11', msg='message for 11', extra=123)
    pub.sendMessage('subtopic11', msg='message for 11', extra=123)
    print_('---- SENT topic1.subtopic11 message ----')

def doSomething2():
    print_('--- SENDING topic1 message ---')
    pub.sendMessage('topic1', msg='message for 1')
    print_('---- SENT topic1 message ----')

class DataMsg(object):
    data1='rrr'
    data2 = 'rrr'
    data3 = 'rrr'

import threading
def callback(data):
    pub.sendMessage('topic2', data=data)

def doSomething3():
    print_('--- SENDING topic2 message ---')
    d = DataMsg()
    d.data1 = 'Test1'

    t = threading.Thread(target=callback, args=(d,))
    # t.setDaemon(True)
    t.start()
    # t.join()
    print_('---- SENT topic2 message ----')

def doSomething4():
    print_('--- SENDING topic_2 message ---')
    pub.sendMessage('topic_2.subtopic_21', arg1="Test")
    print_('---- SENT topic_2 message ----')