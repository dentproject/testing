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
from builtins import object
import logging
from abc import ABCMeta

from enum import Enum

from .EventNameEnum import EventNameEnum
from pubsub import pub
import threading
from . import EventsDefinitionProviders
from Marvell.pytoolsinfra.SysEventManager.BaseSysEventData import BaseSysEventData
from future.utils import with_metaclass

pub.addTopicDefnProvider(EventsDefinitionProviders, pub.TOPIC_TREE_FROM_CLASS)
pub.setTopicUnspecifiedFatal()


class SysEventManager(with_metaclass(ABCMeta, object)):
    """
    This class is the manager class for Sending/Registering for the system events
    """
    _dispatch_sys_event_lock = threading.Lock()
    _register_sys_event_lock = threading.Lock()
    listener_to_id = {}
    id_to_listener = {}
    sync_event_to_id_list = {}
    event_to_id_list = {}
    listener_id = 1

    def __init__(self):
        raise NotImplementedError('ERROR: Cant instantiate abstract class')

    @staticmethod
    def _send_message_bg(event_name, event_data):
        """
        This is a callback function for use in a thread of sending message in the BG

        :param event_name: an Enum type of the event
        :type event_name: EventNameEnum
        :param event_data: The data the sender wants to send to all the listeners
        :type event_data: BaseSysEventData
        :return:
        """
        try:
            pub.sendMessage(event_name, data=event_data)
        except Exception as e:
            logging.debug('Got exception:"{}"\nWhen tried to dispatch: "{}" ----'.format(e, event_name))

    @staticmethod
    def DispatchSysEvent(event_name, event_data, sync=False):
        # type: (EventNameEnum, BaseSysEventData, bool) -> None
        """
        This function sends the event to all the 'listeners' of this kind of event

        :param event_name: an Enum type of the event
        :type event_name: EventNameEnum
        :param event_data: The data the sender wants to send to all the listeners
        :type event_data: BaseSysEventData
        :param sync: will indicate if the Dispatch will be at different thread or it will be blocking
        :return: void
        """

        with SysEventManager._dispatch_sys_event_lock:
            if not sync and event_name not in SysEventManager.sync_event_to_id_list:
                t = threading.Thread(target=SysEventManager._send_message_bg, args=(event_name, event_data,))
                t.start()
            else:
                pub.sendMessage(event_name, data=event_data)

    @staticmethod
    def Register(event_name, callback, sync=False):
        # type: (Enum, (BaseSysEventData,)) -> int
        """
        This function register a listener to messages and will call its callback function when the event is raised

        :param event_name: an Enum type of the event
        :type event_name: EventNameEnum
        :param callback: a function that will be called when the event is raised
        :type callback: must be of format "def listener(cls, data, topic=pub.AUTO_TOPIC)"
                        topic=pub.AUTO_TOPIC -> indicates that the topic name will be sent to the listener
                        automatically according to the registered event
        """

        with SysEventManager._register_sys_event_lock:
            _, success = pub.subscribe(callback, event_name)
            listener_tuple = (callback, event_name)
            if success:
                SysEventManager.listener_id += 1
                SysEventManager.listener_to_id[listener_tuple] = SysEventManager.listener_id
                SysEventManager.id_to_listener[SysEventManager.listener_id] = listener_tuple
                if sync:
                    if event_name in SysEventManager.sync_event_to_id_list:
                        SysEventManager.sync_event_to_id_list[event_name].append(SysEventManager.listener_id)
                    else:
                        SysEventManager.sync_event_to_id_list[event_name] = [SysEventManager.listener_id]

                if event_name in SysEventManager.event_to_id_list:
                    SysEventManager.event_to_id_list[event_name].append(SysEventManager.listener_id)
                else:
                    SysEventManager.event_to_id_list[event_name] = [SysEventManager.listener_id]

            else:  # This callback already regitered to this event
                if listener_tuple not in SysEventManager.listener_to_id:
                    raise Exception('There was a problem registering the callback')

            return SysEventManager.listener_to_id[listener_tuple]


    @staticmethod
    def UnRegister(event_name, callback):
        # type: (EventNameEnum, (BaseSysEventData,)) -> None
        """
        This function unregister a listener to messages and will stop call its callback function when the event is raised

        :param event_name: an Enum type of the event
        :type event_name: EventNameEnum
        :param callback: a function that will be unregister from the event list
        :type callback: must be of format "def listener(cls, data, topic=pub.AUTO_TOPIC)"
                        topic=pub.AUTO_TOPIC -> indicates that the topic name will be sent to the listener
                        automatically according to the registered event
        """
        with SysEventManager._dispatch_sys_event_lock:
            listener_tuple = (callback, event_name)
            if listener_tuple in SysEventManager.listener_to_id:
                pub.unsubscribe(callback, event_name)
                SysEventManager._remove_event(event_name, callback, SysEventManager.listener_to_id[listener_tuple])

    @staticmethod
    def UnRegisterById(listener_id):
        # type: (int) -> None
        """
        This function unregister a listener to messages and will stop call its callback function when the event is raised

        :param listener_id: the id the user got when registered
        :type listener_id: int
        """

        if listener_id not in SysEventManager.id_to_listener:
            raise Exception('There was a problem unregistering the listener.Listener dosn\'t exists')

        with SysEventManager._dispatch_sys_event_lock:
            if listener_id in SysEventManager.id_to_listener:
                callback, event_name = SysEventManager.id_to_listener[listener_id]
                pub.unsubscribe(callback, event_name)
                SysEventManager._remove_event(event_name, callback, listener_id)

    @staticmethod
    def UnRegisterAll():
        # type: () -> None
        """
        This function unregister all listeners to messages and will stop call its callback function when the event is raised
        """
        with SysEventManager._dispatch_sys_event_lock:
            pub.unsubAll()
            SysEventManager._remove_all_events()

    @staticmethod
    def _remove_event(event_name, callback, listener_id):
        """
        This function removes a listener from the list according to the listener ID

        :param event_name: an Enum type of the event
        :type event_name: EventNameEnum
        :param callback: a function that will be unregister from the event list
        :type callback: must be of format "def listener(cls, data, topic=pub.AUTO_TOPIC)"
                        topic=pub.AUTO_TOPIC -> indicates that the topic name will be sent to the listener
                        automatically according to the registered event
        :param listener_id: id of the listener
        :type listener_id: int
        """
        listener_tuple = (callback, event_name)
        if listener_tuple in SysEventManager.listener_to_id:
            SysEventManager.listener_to_id.pop(listener_tuple)

        if listener_id in SysEventManager.id_to_listener:
            SysEventManager.id_to_listener.pop(listener_id)

        if event_name in SysEventManager.sync_event_to_id_list:
            if listener_id in SysEventManager.sync_event_to_id_list[event_name]:
                SysEventManager.sync_event_to_id_list[event_name].remove(listener_id)
                if len(SysEventManager.sync_event_to_id_list[event_name]) == 0:
                    SysEventManager.sync_event_to_id_list.pop(event_name)

        if event_name in SysEventManager.event_to_id_list:
            if listener_id in SysEventManager.event_to_id_list[event_name]:
                SysEventManager.event_to_id_list[event_name].remove(listener_id)
                if len(SysEventManager.event_to_id_list[event_name]) == 0:
                    SysEventManager.event_to_id_list.pop(event_name)

    @staticmethod
    def _remove_all_events():
        """
        This function removes all listeners from the list
        """
        SysEventManager.listener_to_id.clear()
        SysEventManager.id_to_listener.clear()
        SysEventManager.sync_event_to_id_list.clear()
        SysEventManager.event_to_id_list.clear()

    @staticmethod
    def IsEventRegistered(event_name):
        return event_name in event_name in SysEventManager.event_to_id_list

    @staticmethod
    def AddProviderClass(newProvider):
        pub.addTopicDefnProvider(newProvider, pub.TOPIC_TREE_FROM_CLASS)
