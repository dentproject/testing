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

from random import randint, choice
import ipaddress
from pandas import DataFrame, merge
from itertools import chain, combinations
import typing as T

from collections import defaultdict
from PyInfraCommon.GlobalFunctions.Random import Randomize


def cartesianProduct(key1Name, key2Name, list1, list2):
    df1 = DataFrame({'key': 1, key1Name: list1})
    df2 = DataFrame({'key': 1, key2Name: list2})
    out = merge(df1, df2, on='key')[[key1Name, key2Name]]
    return out


def getTGRep(tgPort):
    return ', '.join(tgPort.__str__().split('\n')[:-2])


def powerset(iterable):
    """
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    xs = list(iterable)
    # note we return an iterator rather than a list
    return list(chain.from_iterable(combinations(xs,n) for n in range(len(xs)+1)))


def expectedActualTable(title, actual, expected, **kwargs):
    if isinstance(expected, list):
        status = actual in expected
    else:
        status = actual == expected
    from prettytable import PrettyTable
    x = PrettyTable()
    x.field_names = list(kwargs.keys()) + ['Actual', 'Expected']
    x.add_row(list(kwargs.values()) + [actual, expected])
    return status, x.get_string(title=title)


def nestedSetattr(obj, key, value):
    """
    A more powerful setattr version. Can also set nested attributes.
    For example:

        class A:
            def __init__(self):
                self.b = B()

        class B:
            def __init__(self):
                self.c = C()

        class C:
            def __init__(self):
                self.d = 2

        a = A()

        Then it is possible to set the value of attribute a.b.c.d to 3 this way: attrSetter(a, 'b.c.d', 3)


    :param obj: the object to set the attribute/nested attribute of
    :param key: the attribute/nested attribute name
    :param value: the value to set the attribute/nested attribute
    :return:
    """
    import re
    attribute_parts = key.split(".")
    obj2 = obj
    isList = re.compile(r'(?:[\[])(?P<val>.*)(?:[\]])')
    for a in attribute_parts[:-1]:
        res = isList.findall(a)
        if res:
            a = a.strip(f"[{res[0]}]")
            obj2 = getattr(obj2, a)[res[0]]
        else:
            obj2 = getattr(obj2, a)
    setattr(obj2, attribute_parts[-1], value)


def getRandIp(excludeNetworks=None, attempts=3):
    nets = []
    if excludeNetworks:
        for net in excludeNetworks:
            nets.append(ipaddress.ip_network(net, strict=False))
    for _ in range(attempts):
        randIp = Randomize().IPv4()
        for net in nets:
            if ipaddress.ip_network('{}/32'.format(randIp), strict=False).subnet_of(net):
                break
        else:
            return randIp
    raise Exception


def randIpv4AddrFromNetwork(ipAddr=Randomize().IPv4(), mask=randint(10, 31), excludeAddr=[]):
    net = ipaddress.ip_network('{}/{}'.format(ipAddr, mask), strict=False)
    hosts = list(map(str, net.hosts()))
    if excludeAddr:
        for host in excludeAddr:
            try:
                hosts.remove(host)
            except ValueError:
                pass
    return choice(hosts)


class HandlerNotFound(Exception):
    """Raised if a handler wasn't found"""

    def __init__(self, event: str, handler: T.Callable) -> None:
        super().__init__()
        self.event = event
        self.handler = handler

    def __str__(self) -> str:
        return "Handler {} wasn't found for event {}".format(self.handler, self.event)


class EventNotFound(Exception):
    """Raised if an event wasn't found"""

    def __init__(self, event: str) -> None:
        super().__init__()
        self.event = event

    def __str__(self) -> str:
        return "Event {} wasn't found".format(self.event)


class Observable(object):
    """Event system for python"""

    def __init__(self) -> None:
        self._events = defaultdict(list)  # type: T.DefaultDict[str, T.List[T.Callable]]

    def get_all_handlers(self) -> T.Dict[str, T.List[T.Callable]]:
        """Returns a dict with event names as keys and lists of
        registered handlers as values."""

        events = {}
        for event, handlers in self._events.items():
            events[event] = list(handlers)
        return events

    def get_handlers(self, event: str) -> T.List[T.Callable]:
        """Returns a list of handlers registered for the given event."""

        return list(self._events.get(event, []))

    def is_registered(self, event: str, handler: T.Callable) -> bool:
        """Returns whether the given handler is registered for the
        given event."""

        return handler in self._events.get(event, [])

    def on(
        self, event: str, *handlers: T.Callable
    ) -> T.Callable:  # pylint: disable=invalid-name
        """Registers one or more handlers to a specified event.
        This method may as well be used as a decorator for the handler."""

        def _on_wrapper(*handlers: T.Callable) -> T.Callable:
            """wrapper for on decorator"""
            self._events[event].extend(handlers)
            return handlers[0]

        if handlers:
            return _on_wrapper(*handlers)
        return _on_wrapper

    def off(
        self, event: str = None, *handlers: T.Callable
    ) -> None:  # pylint: disable=keyword-arg-before-vararg
        """Unregisters a whole event (if no handlers are given) or one
        or more handlers from an event.
        Raises EventNotFound when the given event isn't registered.
        Raises HandlerNotFound when a given handler isn't registered."""

        if not event:
            self._events.clear()
            return

        if event not in self._events:
            raise EventNotFound(event)

        if not handlers:
            self._events.pop(event)
            return

        for callback in handlers:
            if callback not in self._events[event]:
                raise HandlerNotFound(event, callback)
            while callback in self._events[event]:
                self._events[event].remove(callback)
        return

    def once(self, event: str, *handlers: T.Callable) -> T.Callable:
        """Registers one or more handlers to a specified event, but
        removes them when the event is first triggered.
        This method may as well be used as a decorator for the handler."""

        def _once_wrapper(*handlers: T.Callable) -> T.Callable:
            """Wrapper for 'once' decorator"""

            def _wrapper(*args: T.Any, **kw: T.Any) -> None:
                """Wrapper that unregisters itself before executing
                the handlers"""

                self.off(event, _wrapper)
                for handler in handlers:
                    handler(*args, **kw)

            return _wrapper

        if handlers:
            return self.on(event, _once_wrapper(*handlers))
        return lambda x: self.on(event, _once_wrapper(x))

    def trigger(self, event: str, *args: T.Any, **kw: T.Any) -> bool:
        """Triggers all handlers which are subscribed to an event.
        Returns True when there were callbacks to execute, False otherwise."""

        callbacks = list(self._events.get(event, []))
        if not callbacks:
            return False

        for callback in callbacks:
            callback(*args, **kw)
        return True
