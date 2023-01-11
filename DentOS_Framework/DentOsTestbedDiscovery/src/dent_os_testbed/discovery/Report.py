"""Report.py

Wrapper for the discovery report JSON.
"""

import copy
import io
import json


class CommitMixin(object):

    def commit(self):
        """Commit this RHS as a LHS.

        Traverse up to the parent, moving the RHS to the LHS.
        """

        ob = self
        while True:

            parent = ob.__dict__['__parent__']
            if parent is None: break
            # stop once we reach the parent

            # get the underlying dict or list for this sub-tree
            if isinstance(ob, (SchemaDict, LeafSchemaDict,)):
                ob_ = ob.__dikt__
            elif isinstance(ob, (SchemaList, LeafSchemaList,)):
                ob_ = ob.__lizt__
            else:
                raise ValueError("invalid child context %s"
                                 % ob.__class__.__name__)

            # perform a setattr/setitem on the parent
            # to commit this attribute/index
            if isinstance(parent, (SchemaDict, LeafSchemaDict,)):
                slot = ob.__dict__['__slot__']
                parent_ = parent.__dict__['__dikt__']
                parent_[slot] = ob_
            elif isinstance(parent, (SchemaList, LeafSchemaList,)):
                item = ob.__dict__['__item__']
                parent_ = parent.__dict__['__lizt__']
                if item < len(parent_):
                    parent_[item] = ob_
                elif item == len(parent_):
                    parent_.append(ob_)
                else:
                    raise IndexError("%s: %s index %d out of range"
                                     % (parent.__class__.__name__,
                                        ob.__class__.__name__,
                                        item,))
            else:
                raise ValueError("invalid parent context %s"
                                 % parent.__class__.__name__)

            ob = parent
            # keep iterating up to the top

class LeafSchemaDict(CommitMixin):

    def __init__(self, dikt):
        self.__dict__['__dikt__'] = dikt
        self.__dict__['__parent__'] = None
        self.__dict__['__slot__'] = None

    def __len__(self):
        return len(self.__dikt__)

    def __getattr__(self, attr, dfl=None):

        if attr == 'get':
            return self.__dikt__.get

        if attr in self.__dikt__:
            return self.__dikt__[attr]

        return dfl

    def __setattr__(self, attr, val):
        """Set a leaf value."""

        self.__dikt__[attr] = val
        # perform the assignment locally

        self.commit()
        # re-attach all of the rvals up to the root object

    def validate(self, data):
        pass

    def replace(self, data):
        self.validate(data)
        data_ = self.__dict__['__dikt__']
        data_.clear()
        data_.update(data)
        self.commit()

class UnknownSchemaDict(LeafSchemaDict):
    pass
# un-expanded schema, TBD

class SchemaDict(CommitMixin):

    __schema_slots__ = {}
    # customize each sub-tree by wrapper class

    def __init__(self, dikt):
        self.__dict__['__dikt__'] = dikt
        self.__dict__['__parent__'] = None
        self.__dict__['__slot__'] = None

    def __len__(self):
        return len(self.__dikt__)

    def __getattr__(self, attr, dflt=None):
        if attr == 'get':
            return self.__dikt__.get
        if attr not in self.__schema_slots__:
            raise AttributeError("%s: invalid slot %s"
                                 % (self.__class__.__name__, attr,))
        cls = self.__schema_slots__[attr]

        # attr exists, trigger the constructor and move on
        if attr in self.__dikt__:
            return cls(self.__dikt__[attr])

        # atomic leaf values do not support sub-assignment
        if issubclass(cls, (int, str, float,)):
            return dflt or None

        if issubclass(cls, (LeafSchemaDict, SchemaDict, dict,)):
            dflt = dflt or {}
        elif issubclass(cls, (SchemaList, LeafSchemaList, list,)):
            dflt = []
        else:
            raise ValueError("invalid %s attr %s"
                             % (cls.__name__, attr,))

        # this attribute does not exist.
        # 1. create a dummy rval that represents the new/empty
        #    subtree
        # 2. attach a reference to the direct parent
        # 3. return the dummy rval
        # later on, we can use the parent reference(s)
        # to turn this from an rval to an lval
        newsubtree = dflt
        ob = cls(newsubtree)
        ob.__dict__['__parent__'] = self
        ob.__dict__['__slot__'] = attr
        return ob

    def __setattr__(self, attr, val):
        """Set a leaf value."""

        if attr not in self.__schema_slots__:
            raise AttributeError("%s: invalid slot %s"
                                 % (self.__class__.__name__, attr,))
        cls = self.__schema_slots__[attr]

        if issubclass(cls, (int, str, float,)):

            self.__dikt__[attr] = cls(val)
            # perform the assignment locally

            self.commit()
            # re-attach all of the rvals up to the root object

            return

        raise ValueError("%s: cannot assign non-leaf %s"
                         % (self.__class__.__name__, attr,))

    def validate(self, data):
        for k, v in data.items():
            if k not in self.__schema_slots__:
                raise AttributeError("%s: invalid slot %s"
                                     % (self.__class__.__name__, k,))
            cls = self.__schema_slots__[k]
            if issubclass(cls, (SchemaDict, LeafSchemaDict,)):
                getattr(self, k).validate(v)
            if issubclass(cls, (SchemaList, LeafSchemaList,)):
                getattr(self, k).validate(v)

    def replace(self, data):
        self.validate(data)
        data_ = self.__dict__['__dikt__']
        data_.clear()
        data_.update(data)
        self.commit()

class LeafSchemaList(CommitMixin):
    __item_klass__ = UnknownSchemaDict

    def __init__(self, lizt):
        self.__lizt__ = lizt
        self.__dict__['__parent__'] = None
        self.__dict__['__item__'] = None

    def __len__(self):
        return len(self.__lizt__)

    def __getitem__(self, item):

        # already in the list
        if item < len(self.__lizt__):
            return self.__item_klass__(self.__lizt__[item])

        # more than a simple append
        if item > len(self.__lizt__):
            raise IndexError("%s: list index %d out of range"
                             % (self.__class__.__name__, item,))

        dflt = {}

        # reference to an object one past the end of the list,
        # 1. create a dummy rval that represents the new/empty
        #    subtree
        # 2. attach a reference to the direct parent
        # 3. return the dummy rval
        # later on, we can use the parent reference(s)
        # to turn this from an rval to an lval (by inserting it
        # into the parent's lval)
        newitem = dflt
        ob = self.__item_klass__(newitem)
        ob.__dict__['__parent__'] = self
        ob.__dict__['__item__'] = item
        return ob

    def __setitem__(self, item, val):

        # index already exists, perform a leaf re-assignment
        if item < len(self.__lizt__):
            self.__lizt__[item] = val
            self.commit()
            return

        # index is just past the end, assume we can append
        if item == len(self.__lizt__):
            self.__lizt__.append(val)
            self.commit()
            return

        # out of range
        raise IndexError("%s: list index %d out of range"
                         % (self.__class__.__name__, item,))

    def filter(self, fn=None, **kwargs):

        res = []
        for idx, item in enumerate(self.__lizt__):
            ob = self.__item_klass__(item)
            if fn is not None and fn(ob):
                res.append(ob)
        return res

    def validate(self, data):
        pass

    def replace(self, data):
        self.validate(data)
        data_ = self.__lizt__
        del data_[:]
        data_.extend(data)
        self.commit()

class UnknownSchemaList(LeafSchemaList):
    pass
# list of unresolved items, yet to be spec'd out

class SchemaList(CommitMixin):

    __item_klass__ = SchemaDict
    # wrapper class for each list item

    def __init__(self, lizt):
        self.__lizt__ = lizt
        self.__dict__['__parent__'] = None
        self.__dict__['__item__'] = None

    def __len__(self):
        return len(self.__lizt__)

    def __getitem__(self, item):

        # already in the list
        if item < len(self.__lizt__):
            return self.__item_klass__(self.__lizt__[item])

        # more than a simple append
        if item > len(self.__lizt__):
            raise IndexError("%s: list index %d out of range"
                             % (self.__class__.__name__, item,))

        # atomic leaf values do not support auto-append
        if issubclass(self.__item_klass__, (int, str, float,)):
            raise IndexError("%s: list index %d out of range"
                             % (self.__class__.__name__, item,))

        if issubclass(self.__item_klass__, (LeafSchemaDict, SchemaDict, dict,)):
            dflt = {}
        elif issubclass(self.__item_klass__, (SchemaList, list,)):
            dflt = []
        else:
            raise ValueError("invalid index %s (%s)"
                             % (item, self.__item_klass__,))

        # reference to an object one past the end of the list,
        # 1. create a dummy rval that represents the new/empty
        #    subtree
        # 2. attach a reference to the direct parent
        # 3. return the dummy rval
        # later on, we can use the parent reference(s)
        # to turn this from an rval to an lval (by inserting it
        # into the parent's lval)
        newitem = dflt
        ob = self.__item_klass__(newitem)
        ob.__dict__['__parent__'] = self
        ob.__dict__['__item__'] = item
        return ob

    def __setitem__(self, item, val):

        # assign or append
        if issubclass(self.__item_klass__, (int, str, float,)):

            # index already exists, perform a leaf re-assignment
            if item < len(self.__lizt__):
                self.__lizt__[item] = val
                self.commit()
                return

            # index is just past the end, assume we can append
            if item == len(self.__lizt__):
                self.__lizt__.append(val)
                self.commit()
                return

            # out of range
            raise IndexError("%s: list index %d out of range"
                             % (self.__class__.__name__, item,))

        raise ValueError("%s: cannot assign non-leaf %s at %d"
                         % (self.__class__.__name__, self.__item_klass__, item,))

    def filter(self, fn=None, **kwargs):

        res = []
        for idx, item in enumerate(self.__lizt__):
            ob = self.__item_klass__(item)
            if fn is not None and not fn(ob): continue
            unmatched = False
            for k, v in kwargs.items():
                if getattr(ob, k) != v:
                    unmatched = True
                    break
            if not unmatched:
                res.append(ob)
        return res

    def validate(self, data):
        cls = self.__item_klass__
        for idx, item in enumerate(data):
            if issubclass(cls, (SchemaDict, LeafSchemaDict,)):
                self[idx].validate(item)
            if issubclass(cls, (SchemaList, LeafSchemaList,)):
                self[idx].validate(item)

    def replace(self, data):
        self.validate(data)
        data_ = self.__lizt__
        del data_[:]
        data_.extend(data)
        self.commit()

class PartitionSchemaDict(SchemaDict):
    __schema_slots__ = {'mount' : str,
                        'device' : str,
                        'size' : int,
                        'free' : int,
                        'opts' : str,}

class PartitionItemList(SchemaList):
    __item_klass__ = PartitionSchemaDict

class BaseboardSchemaDict(SchemaDict):
    __schema_slots__ = {'platform' : str,
                        'serial' : str,
                        'cpu_type' : str,
                        'cpu_speed' : int,
                        'cpu_core_count' : int,
                        'memory_total' : int,
                        'memory_free' : int,
                        'partitions' : PartitionItemList,}

class FruItemSchemaDict(SchemaDict):
    __schema_slots__ = {'name' : str,
                        'model' : str,
                        'serial' : str,}

class FruItemList(SchemaList):
    __item_klass__ = FruItemSchemaDict

class FruSchemaDict(SchemaDict):
    __schema_slots__ = {'fans' : FruItemList,
                        'psus' : FruItemList,
                        'serial' : FruItemList,}

class PlatformSchemaDict(SchemaDict):
    __schema_slots__ = {'baseboard' : BaseboardSchemaDict,
                        'software' : LeafSchemaDict,
                        'fru' : FruSchemaDict,}

class SfpSchemaDict(SchemaDict):
    __schema_slots__ = {'vendor' : str,
                        'model' : str,
                        'serial' : str,}

class InterfaceSchemaDict(SchemaDict):
    __schema_slots__ = {'name' : str,
                        'speed' : int,
                        'media' : str,
                        'configured_state' : str,
                        'peer_device_id' : str,
                        'peer_interface' : str,
                        'sfp' : SfpSchemaDict,}

class InterfacesSchemaList(SchemaList):
    __item_klass__ = InterfaceSchemaDict

class InterfaceNamesSchemaList(SchemaList):
    __item_klass__ = str

class LagsSchemaDict(SchemaDict):
    __schema_slots__ = {'name' : str,
                        'interfaces' : InterfaceNamesSchemaList,}

class LagsSchemaList(SchemaList):
    __item_klass__ = LagsSchemaDict

class L1SchemaDict(SchemaDict):
    __schema_slots__ = {'management_mac' : str,
                        'interfaces' : InterfacesSchemaList,
                        'lags' : LagsSchemaList,}

class VlanSchemaDict(SchemaDict):
    __schema_slots__ = {'vlan_id' : int,
                        'access_ports' : InterfaceNamesSchemaList,
                        'trunk_ports' : InterfaceNamesSchemaList,}

class VlansSchemaList(SchemaList):
    __item_klass__ = VlanSchemaDict

class BridgeSchemaDict(SchemaDict):
    ___schema_slots__ = {'name' : str,
                         'interfaces' : InterfaceNamesSchemaList,
                         'stp' : bool,}

class BridgesSchemaList(SchemaList):
    __item_klass__ = BridgeSchemaDict

class L2SchemaDict(SchemaDict):
    __schema_slots__ = {'vlans' : VlansSchemaList,
                        'bridges' : BridgesSchemaList,}

class BgpNeighSchemaDict(SchemaDict):
    __schema_slots__ = {'neighbor' : str,
                        'as_' : int,
                        'up' : str,
                        'state' : str,}

class BgpNeighSchemaList(SchemaList):
    __item_klass__ = BgpNeighSchemaDict

class BgpSchemaDict(SchemaDict):
    __schema_slots__ = {'as_' : int,
                        'router' : str,
                        'neighbors' : BgpNeighSchemaList,}

class OspfNeighSchemaDict(SchemaDict):
    __schema_slots__ = {'address' : str,
                        'router_id' : str,
                        'priority' : int,
                        'state' : str,
                        'interface' : str,}

class OspfNeighSchemaList(SchemaList):
    __item_klass__ = OspfNeighSchemaDict

class OspfSchemaDict(SchemaDict):
    __schema_slots__ = {'router_id' : str,
                        'neighbors' : OspfNeighSchemaList,}

class L3SchemaDict(SchemaDict):
    __schema_slots__ = {'management_ip' : str,
                      'routes' : UnknownSchemaList,
                      'acls' : UnknownSchemaDict,
                      'bgp' : BgpSchemaDict,
                      'ospf' : OspfSchemaDict,}

class DeviceNetworkSchemaDict(SchemaDict):
    __schema_slots__ = {'layer1' : L1SchemaDict,
                        'layer2' : L2SchemaDict,
                        'layer3' : L3SchemaDict,}

class DutSchemaDict(SchemaDict):
    __schema_slots__ = {'device_id' : str,
                        'platform' : PlatformSchemaDict,
                        'network' : DeviceNetworkSchemaDict,}

class DutsSchemaList(SchemaList):
    __item_klass__ = DutSchemaDict

class InfrastructureSchemaDict(SchemaDict):
    __schema_slots__ = {'device_id' : str,
                        'network' : DeviceNetworkSchemaDict,}

class InfrastructureSchemaList(SchemaList):
    __item_klass__ = InfrastructureSchemaDict

class TestbedInterfaceSchemaDict(SchemaDict):
    __schema_slots__ = {'device_id' : str,
                        'interface' : str,}

class TestbedInterfacesSchemaList(SchemaList):
    __item_klass__ = TestbedInterfaceSchemaDict

class TestbedVlanSchemaDict(SchemaDict):
    __schema_slots__ = {'vlan_id' : int,
                        'access_ports' : TestbedInterfacesSchemaList,
                        'trunk_ports' : TestbedInterfacesSchemaList,}

class TestbedVlansSchemaList(SchemaList):
    __item_klass__ = TestbedVlanSchemaDict

class TestbedL2SchemaDict(SchemaDict):
    __schema_slots__ = {'vlans' : TestbedVlansSchemaList,}

class TestbedBgpRouterSchemaDict(SchemaDict):
    __schema_slots__ = {'router' : str,
                        'device_id' : str,}

class TestbedBgpRoutersSchemaList(SchemaList):
    __item_klass__ = TestbedBgpRouterSchemaDict

class TestbedBgpSchemaDict(SchemaDict):
    __schema_slots__ = {'routers' : TestbedBgpRoutersSchemaList,}

class TestbedOspfRouterSchemaDict(SchemaDict):
    __schema_slots__ = {'address' : str,
                        'router_id' : str,
                        'device_id' : str,}

class TestbedOspfRoutersSchemaList(SchemaList):
    __item_klass__ = TestbedOspfRouterSchemaDict

class TestbedOspfSchemaDict(SchemaDict):
    __schema_slots__ = {'routers' : TestbedOspfRoutersSchemaList,}

class TestbedL3SchemaDict(SchemaDict):
    __schema_slots__ = {'bgp' : TestbedBgpSchemaDict,
                        'ospf' : TestbedOspfSchemaDict,}

class TestbedNetworkSchemaDict(SchemaDict):
    __schema_slots__ = {'layer2' : TestbedL2SchemaDict,
                        'layer3' : TestbedL3SchemaDict,}

class ReportSchemaDict(SchemaDict):
    __schema_slots__ = {'attributes' : LeafSchemaDict,
                        'duts' : DutsSchemaList,
                        'infrastructure' : InfrastructureSchemaList,
                        'network' : TestbedNetworkSchemaDict,}

class Report(object):

    def __init__(self, jsonData):
        self.data = ReportSchemaDict(jsonData)

    def clone(self, jsonData):
        return Report(copy.deepcopy(jsonData))

    @classmethod
    def fromData(cls, jsonData):
        return cls(jsonData)

    @classmethod
    def fromPath(cls, path):
        with io.open(path, "rt") as fd:
            data = json.load(fd)
        return cls(data)

    @classmethod
    def fromFd(cls, fd):
        data = json.read(fd)
        return cls(data)

    def asDict(self):
        return self.data.__dikt__

    # XXX roth -- fill me in with helper methods to traverse the JSON

    # quick access to top-level attributes in the report

    @property
    def attributes(self):
        return self.data.attributes

    @property
    def operator(self):
        return self.attributes.get('operator', None)

    @property
    def topology(self):
        return self.attributes.get('topology', None)

    @property
    def duts(self):
        return self.data.duts

    @property
    def infrastructure(self):
        return self.data.infrastructure

    @property
    def network(self):
        return self.data.network
