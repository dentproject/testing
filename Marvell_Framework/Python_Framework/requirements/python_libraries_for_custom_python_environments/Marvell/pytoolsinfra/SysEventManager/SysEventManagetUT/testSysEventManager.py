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
from pubsub.core import TopicDefnError, ListenerMismatchError

from Marvell.pytoolsinfra.SysEventManager.SysEventManager import *
from unittest import TestCase
import logging
from . import new_provider_events

logging_level = logging.INFO # DEBUG / INFO
logging.basicConfig(level=logging_level,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )


class DataMsg(BaseSysEventData):
    data1 = 'rrr'


class TestSysEventManager(TestCase):
    d = DataMsg('Test')
    d.data1 = 'Test1'
    e = threading.Event()
    e_main_thread = threading.Event()
    registered_id = 0
    new_provider_event = 'topic_1'
    not_registered_event = 'con.cof'

    def bad_listener(self, msg, topic=pub.AUTO_TOPIC):
        pass

    @classmethod
    def register_to_event(cls):
        cls.registered_id = SysEventManager.Register(EventNameEnum.COMM_CONNECT_EVENT, cls.listener)

    @classmethod
    def register_to_event_sync(cls):
        cls.sync_registered_id = SysEventManager.Register(EventNameEnum.COMM_DISCONNECT_EVENT, cls.listener, sync=True)

    @classmethod
    def register_to_disconnect_async(cls):
        cls.async_registered_id = SysEventManager.Register(EventNameEnum.COMM_DISCONNECT_EVENT, cls.listener)

    @classmethod
    def register_to_connection_lost_event(cls):
        cls.connection_lost_registered_id = SysEventManager.Register(EventNameEnum.COMM_CONNECTION_LOST_EVENT, cls.listener)

    @classmethod
    def listener(cls, data, topic=pub.AUTO_TOPIC):
        info = 'Method Listener received "%s" message: %s sender-name: %s'
        logging.debug(info % (topic.getName(), repr(data.data1), repr(data.sender_name)))
        if threading.currentThread().getName() == 'MainThread':
            cls.e_main_thread.set()
        else:
            cls.e.set()

    @classmethod
    def setUpClass(cls):
        cls.register_to_event()
        cls.register_to_event_sync()
        cls.register_to_connection_lost_event()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.e.clear()
        self.e_main_thread.clear()

    def tearDown(self):
        pass

    def test_send_message_async(self):
        logging.debug('--- SENDING communication.connect async message ---')
        self.d.sender_name = 'test_send_message_async'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, self.d)
        event_is_set = self.e.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.connect async message ----')
        else:
            logging.error('---- No listener for communication.connect async message ----')

    def test_send_message_sync(self):
        logging.debug('--- SENDING communication.connect sync message ---')
        self.d.sender_name = 'test_send_message_sync'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.connect sync message ----')
        else:
            logging.error('---- No listener for communication.connect sync message ----')

    def test_send_message_async_with_sync_event(self):
        logging.debug('--- SENDING communication.disconnect async message ---')
        self.d.sender_name = 'test_send_message_async_with_sync_event'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_DISCONNECT_EVENT, self.d)
        event_is_set = self.e_main_thread.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.disconnect async message ----')
        else:
            logging.error('---- No listener for communication.disconnect async message ----')

    def test_send_message_sync_with_sync_event(self):
        logging.debug('--- SENDING communication.disconnect sync message ---')
        self.d.sender_name = 'test_send_message_sync_with_sync_event'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_DISCONNECT_EVENT, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.connect sync message ----')
        else:
            logging.error('---- No listener for communication.connect sync message ----')

    def test_send_message_async_with_sync_event_after_unregister(self):
        SysEventManager.UnRegister(EventNameEnum.COMM_DISCONNECT_EVENT, self.listener)
        self.register_to_disconnect_async()

        logging.debug('--- SENDING communication.disconnect async message ---')
        self.d.sender_name = 'test_send_message_async_with_sync_event_after_unregister'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_DISCONNECT_EVENT, self.d)
        event_is_set = self.e.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.disconnect async message ----')
        else:
            logging.error('---- No listener for communication.disconnect async message ----')

        SysEventManager.UnRegister(EventNameEnum.COMM_DISCONNECT_EVENT, self.listener)
        self.register_to_event_sync()

    def test_send_message_sync_with_sync_event_after_unregister(self):
        SysEventManager.UnRegister(EventNameEnum.COMM_DISCONNECT_EVENT, self.listener)
        self.register_to_disconnect_async()

        logging.debug('--- SENDING communication.disconnect sync message ---')
        self.d.sender_name = 'test_send_message_sync_with_sync_event_after_unregister'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_DISCONNECT_EVENT, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.disconnect sync message ----')
        else:
            logging.error('---- No listener for communication.disconnect sync message ----')

        SysEventManager.UnRegister(EventNameEnum.COMM_DISCONNECT_EVENT, self.listener)
        self.register_to_event_sync()

    def test_send_message_async_after_unregister(self):
        SysEventManager.UnRegister(EventNameEnum.COMM_CONNECT_EVENT, self.listener)

        logging.debug('--- SENDING communication.connect async message ---')
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, self.d)
        event_is_set = self.e.wait(1)
        self.assertFalse(event_is_set)
        if event_is_set:
            logging.error('---- SENT communication.connect async message ----')
        else:
            logging.debug('---- GOOD - No listener for communication.connect async message ----')

        self.register_to_event()

    def test_send_message_sync_after_unregister(self):
        SysEventManager.UnRegister(EventNameEnum.COMM_CONNECT_EVENT, self.listener)
        logging.debug('--- SENDING communication.connect sync message ---')
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(1)
        self.register_to_event()
        self.assertFalse(event_is_set)
        if event_is_set:
            logging.error('---- SENT communication.connect sync message ----')
        else:
            logging.debug('---- GOOD - No listener for communication.connect sync message ----')

    def test_send_unpredefinemessage_sync(self):
        logging.debug('--- SENDING UnPreDefineMessage message ---')
        self.assertRaises(TopicDefnError, SysEventManager.DispatchSysEvent, self.not_registered_event, self.d, sync=True)

        event_is_set = self.e_main_thread.wait(1)
        self.assertFalse(event_is_set)
        logging.debug('---- SENT UnPreDefineMessage message ----')

    def test_send_unpredefinemessage_async(self):
        logging.debug('--- SENDING UnPreDefineMessage async message ---')
        SysEventManager.DispatchSysEvent('con.cof', self.d)
        event_is_set = self.e_main_thread.wait(1)
        self.assertFalse(event_is_set)
        logging.debug('---- SENT UnPreDefineMessage async message ----')

    def test_register_unpredefinemessage(self):
        logging.debug('--- Try register UnPreDefineMessage message ---')
        self.assertRaises(TopicDefnError, SysEventManager.Register, 'con.cof', self.listener)

    def test_register_badlistener(self):
        logging.debug('--- Try register UnPreDefineMessage message ---')
        self.assertRaises(ListenerMismatchError, SysEventManager.Register, EventNameEnum.COMM_CONNECT_EVENT,
                          self.bad_listener)

    def test_add_new_provider(self):
        logging.debug('--- Try send new event from the new provider befor adding it ---')
        self.assertRaises(TopicDefnError, SysEventManager.DispatchSysEvent, self.new_provider_event, self.d, sync=True)

        logging.debug('--- Adding new provider message ---')
        SysEventManager.AddProviderClass(new_provider_events)
        logging.debug('--- Try send new event from the new provider message ---')
        id = SysEventManager.Register(self.new_provider_event, self.listener)

        self.d.sender_name = 'test_add_new_provider'
        SysEventManager.DispatchSysEvent(self.new_provider_event, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.connect async message ----')
        else:
            logging.error('---- No listener for communication.connect async message ----')

        SysEventManager.UnRegisterById(id)

    def test_unregister_by_id(self):
        SysEventManager.UnRegisterById(self.registered_id)
        logging.debug('--- SENDING communication.connect sync message ---')
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECT_EVENT, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(1)
        self.register_to_event()
        self.assertFalse(event_is_set)
        if event_is_set:
            logging.error('---- SENT communication.connect sync message ----')
        else:
            logging.debug('---- GOOD - No listener for communication.connect sync message ----')

    def test_getting_same_id_for_same_register(self):
        logging.debug('---- try to register to communication.connect sync message ----')
        new_id = SysEventManager.Register(EventNameEnum.COMM_CONNECT_EVENT, self.listener)
        logging.debug('---- Checking the id for the second registration ----')
        self.assertEqual(new_id, self.registered_id)

    def test_is_event_registered(self):
        self.assertTrue(SysEventManager.IsEventRegistered(EventNameEnum.COMM_CONNECT_EVENT))

    def test_is_event_registered_after_unregister(self):
        SysEventManager.UnRegisterById(self.registered_id)
        self.assertFalse(SysEventManager.IsEventRegistered(EventNameEnum.COMM_CONNECT_EVENT))
        self.register_to_event()

    def test_send_connection_lost_message_async(self):
        logging.debug('--- SENDING communication.connection_lost async message ---')
        self.d.sender_name = 'test_send_connection_lost_message_async'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECTION_LOST_EVENT, self.d)
        event_is_set = self.e.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.connection_lost async message ----')
        else:
            logging.error('---- No listener for communication.connection_lost async message ----')

    def test_send_connection_lost_message_sync(self):
        logging.debug('--- SENDING communication.connection_lost sync message ---')
        self.d.sender_name = 'test_send_connection_lost_message_sync'
        SysEventManager.DispatchSysEvent(EventNameEnum.COMM_CONNECTION_LOST_EVENT, self.d, sync=True)
        event_is_set = self.e_main_thread.wait(2)
        self.assertTrue(event_is_set)
        if event_is_set:
            logging.debug('---- SENT communication.connection_lost sync message ----')
        else:
            logging.error('---- No listener for communication.connection_lost sync message ----')