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
from __future__ import print_function

from builtins import object
from pubsub import pub
from pubsub.py2and3 import print_


# ------------ create some listeners --------------

class Listener(object):
    def onTopic11(self, msg, extra=None):
        print_('Method Listener.onTopic11 received: ', repr(msg), repr(extra))

    def onTopic1(self, msg, topic=pub.AUTO_TOPIC):
        info = 'Method Listener.onTopic1 received "%s" message: %s'
        print_(info % (topic.getName(), repr(msg)))

    def onTopic2(self, data, topic=pub.AUTO_TOPIC):
        info = 'Method Listener.onTopic2 received "%s" message: %s'
        print_(info % (topic.getName(), repr(data.data1)))

    def onTopic_2(self, arg1, topic=pub.AUTO_TOPIC):
        info = 'Method Listener.onTopic_2 received "%s" message: %s'
        print_(info % (topic.getName(), arg1))

    def __call__(self, **kwargs):
        print_('Listener instance received: ', kwargs)

def snoop(topicObj=pub.AUTO_TOPIC, **mesgData):
     print('topic "%s": %s' % (topicObj.getName(), mesgData))

listenerObj = Listener()


def listenerFn(msg, extra=None):
    print_('Function listenerFn received: ', repr(msg), repr(extra))

# ------------ subscribe listeners ------------------

pub.subscribe(snoop, pub.ALL_TOPICS)
pub.subscribe(listenerObj, pub.ALL_TOPICS) # via its __call__

pub.subscribe(listenerFn, 'topic1.subtopic11')
pub.subscribe(listenerObj.onTopic11, 'topic1.subtopic11')

pub.subscribe(listenerObj.onTopic1, 'topic1')

# import kwargs_topics
# pub.addTopicDefnProvider( kwargs_topics, pub.TOPIC_TREE_FROM_CLASS )
# pub.setTopicUnspecifiedFatal(True)

pub.subscribe(listenerObj.onTopic2, 'topic2')
pub.subscribe(listenerObj.onTopic_2, 'topic_2.subtopic_21')

pub.subscribe(snoop, 'topic1.subtopic11')
pub.subscribe(snoop, 'topic_2.subtopic_21')
pub.subscribe(snoop, 'topic1.subtopic11')


# listener_to_id = {}
# id_to_listener = {}
# id = 1

# l1 = (listenerObj.onTopic2, 'topic2')
# l2 = (listenerObj.onTopic2, 'topic2')
# print (l1 == l2)
# listener_to_id[l1] = id
# id_to_listener[id] = l1

# print(listener_to_id)
# print(id_to_listener)

# print (listener_to_id.has_key(l1))
# print(id_to_listener[id][1])
#
# a,b = id_to_listener[id]
# print (a,b)

