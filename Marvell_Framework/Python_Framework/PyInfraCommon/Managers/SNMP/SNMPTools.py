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

#from PyInfraCommon.Globals.Logger.GlobalTestLogger import *
from builtins import str
from builtins import object
from ..SNMP.errorHandlers import SNMPToolError, ArgumentError, SnmpError
from pysnmp.entity.rfc3413.oneliner import cmdgen
from abc import ABCMeta, abstractmethod
from enum import Enum
from ..SNMP.SNMPTools_OSC import *
from enum import IntEnum
from pysnmp.smi import builder, view
from pysnmp.smi.error import SmiError
from future.utils import with_metaclass

class SnmpProtocolVersion(IntEnum):
    """
    SNMP Protocol version enumerator
    """
    v1 = 1
    v2 = 2
    v3 = 3


class USMAuthProtocol(IntEnum):
    """
    Hash protocol used for authentication
    """
    usm_NoAuth = 0 # No Authentication Protocol.
    usm_MD5 = 1 # The HMAC-MD5-96 Digest Authentication Protocol
    usm_SHA = 2 # The HMAC-SHA-96 Digest Authentication Protocol

    @classmethod
    def HasMember(cls, memeber):
        return (any(memeber == item.value for item in cls))


SnmpV3AuthProtocolMap = {
    USMAuthProtocol.usm_NoAuth: cmdgen.usmNoAuthProtocol,
    USMAuthProtocol.usm_MD5: cmdgen.usmHMACMD5AuthProtocol,
    USMAuthProtocol.usm_SHA: cmdgen.usmHMACSHAAuthProtocol
}


class USMPrivProtocol(IntEnum):
    """
    Encryption protocol enumerator
    """
    usm_NoPriv = 0 # No Privacy Protocol
    usm_DES = 1 # The CBC-DES Symmetric Encryption Protocol
    usm_3DES = 2 # The 3DES-EDE Symmetric Encryption Protocol
    usm_AES128 = 3 # The CFB128-AES-128 Symmetric Encryption Protocol
    usm_AES192 = 4 # The CFB128-AES-192 Symmetric Encryption Protocol
    usm_AES256 = 5 #The CFB128-AES-256 Symmetric Encryption Protocol
    usm_BlumentalAES192 = 6 #The CFB128-AES-192 Symmetric Encryption Protocol
    usm_BlumentalAES256 = 7 #The CFB128-AES-256 Symmetric Encryption Protocol

    @classmethod
    def HasMember(cls, memeber):
        return (any(memeber == item.value for item in cls))

SnmpV3PrivProtocolMap = {
    USMPrivProtocol.usm_NoPriv: cmdgen.usmNoPrivProtocol,
    USMPrivProtocol.usm_DES: cmdgen.usmDESPrivProtocol,
    USMPrivProtocol.usm_3DES: cmdgen.usm3DESEDEPrivProtocol,
    USMPrivProtocol.usm_AES128: cmdgen.usmAesCfb128Protocol,
    USMPrivProtocol.usm_AES192: cmdgen.usmAesCfb192Protocol,
    USMPrivProtocol.usm_AES256: cmdgen.usmAesCfb256Protocol,
    USMPrivProtocol.usm_BlumentalAES192: cmdgen.usmAesBlumenthalCfb192Protocol,
    USMPrivProtocol.usm_BlumentalAES256: cmdgen.usmAesBlumenthalCfb256Protocol
}

class SnmpManager(object):
    """
    SNMP manager class responsible to return a relevant instance either v1v2 or v3
    """
    @classmethod
    def get(cls,snmpVersion):
        """
        Factory method that returns the relevant instance suitable for SNMP protocol version
        :param snmpVersion: SnmpProtocolVersion (v1/v2/v3)
        :type snmpVersion: SnmpProtocolVersion
        :return: SNMP object instance
        """
        function_name = cls.__name__
        if snmpVersion == SnmpProtocolVersion.v1 or snmpVersion == SnmpProtocolVersion.v2:
            return SNMPv1v2c(snmpVersion)
        elif snmpVersion == SnmpProtocolVersion.v3:
            return SNMPv3()
        else:
            # Replace with environemnt comaptible exception
            #assert 0, "Bad SNMP Manager argument: " + snmpVersion
            raise ArgumentError("Bad SNMP Manager argument: {}.".format(snmpVersion), function_name)


class SnmpInputParams(object):
    def __init__(self):
        self.ip = None
        self.port = None
        self.timeout = None
        self.retries = None
        self.ReadWriteCommunity = None
        self.ReadOnlyCommunity = None
        self.ReadWrite_UserName = None
        self.ReadWrite_AuthKey = None
        self.ReadWrite_PrivKey = None
        self.ReadWrite_AuthProtocol = None
        self.ReadWrite_PrivProtocol = None
        self.ReadOnly_UserName = None
        self.ReadOnly_AuthKey = None
        self.ReadOnly_PrivKey = None
        self.ReadOnly_AuthProtocol = None
        self.ReadOnly_PrivProtocol = None


class SnmpBasic(with_metaclass(ABCMeta, object)):
    class __MibManager(object):
        def __init__(self):
            # MIB Builder manages pysnmp MIBs
            self.Builder = builder.MibBuilder()
            # MIB View Controller implements various queries to loaded MIBs
            self.ViewController = view.MibViewController(self.Builder)

        def AddMibPath(self, *path):
            """Add an additional directory to the MIB search path.
            :param path: path to additional MIBs
            """
            mib_path = self.Builder.getMibPath() + path
            self.Builder.setMibPath(*mib_path)

        def LoadMibs(self, *moduleList):
            function_name = self.LoadMibs.__name__
            for module in moduleList:
                try:
                    self.Builder.loadModules(module)
                except SmiError as e:
                    raise SnmpError(str(e), function_name)

    def __init__(self):
        self.InputParams = SnmpInputParams()
        self.UdpTransportTarget = None
        self.SecurityDataReadWrite = None
        self.SecurityDataReadOnly = None
        self.SNMPMibManager = self.__MibManager()

    def SetTrasnportLayerParams(self, ip_addr, port_id=161, timeout_val=1, retries_num=5):
        """
        :param ip_addr: Hostname or Ip address string
        :type ip_addr: str
        :param port_id: L4 port number
        :type port_id: int
        :param timeout_val: Response timeout in seconds
        :type timeout_val: int
        :param retries_num: Maximum number of request retries, 0 retries means just a single request.
        :type retries_num: int
        """
        function_name =  self.SetTrasnportLayerParams.__name__

        if 1 <= port_id <= 65535:
            self.InputParams.port = port_id
        else:
            raise ArgumentError("Invalid L4 port number: " + str(port_id) + ". Should be an integer in range 0-65535.",
                                function_name)

        if isinstance(timeout_val, int) and timeout_val >= 0:
            self.InputParams.timeout = timeout_val
        else:
            raise ArgumentError("Illegal timeout value: " + str(timeout_val) + ". Should be a positive integer or "
                                                                               "zero.",
                                function_name)

        if isinstance(retries_num, int) and retries_num >= 0:
            self.InputParams.retries = retries_num
        else:
            raise ArgumentError("Illegal retries value: " + str(retries_num) + ". Should be a positive integer or "
                                                                               "zero.",
                                function_name)


        if IsValidIpv4Address(ip_addr) or IsValidIpv6Address(ip_addr):
            self.InputParams.ip = ip_addr
            if IsValidIpv4Address(ip_addr):
                self.UdpTransportTarget = cmdgen.UdpTransportTarget((self.InputParams.ip, self.InputParams.port),
                                                                    self.InputParams.timeout,
                                                                    self.InputParams.retries)
            else:
                self.UdpTransportTarget = cmdgen.Udp6TransportTarget((self.InputParams.ip, self.InputParams.port),
                                                                     self.InputParams.timeout,
                                                                     self.InputParams.retries)
        else:
            raise ArgumentError("Illegal IP address: " + ip_addr + ". Should be a valid Ipv4 or Ipv6 "
                                                                       "adress.",
                                function_name)


    #@abstractmethod
    def Get(self, oid):
        """
        :param oid: Snmp Object Id
        :type oid: tuple
        :return: Query result list
        """
        function_name = self.Get.__name__
        (errorIndication, errorStatus,
         errorIndex, varBinds) = cmdgen.CommandGenerator().getCmd(
           self.SecurityDataReadOnly,
           self.UdpTransportTarget,
            oid,
            lookupMib=False)

        # Predefine our results list
        results = []

        if errorIndication:
            raise SnmpError(errorIndication, function_name)
        else:
            if errorStatus:
                raise SnmpError('%s at %s\n' %
                               (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1] or '?'), function_name)
            else:
                for name, val in varBinds:
                    results.append(val)

        return results

    #@abstractmethod
    def GetBulk(self, *oids):
        """
        :param oid: Snmp Object Id
        :return: Query result list
        """
        function_name = self.GetBulk.__name__

        # Predefine our snmpRequest list
        snmpRequest = []
        for oid in oids:
            snmpRequest.append(oid,)

        (errorIndication, errorStatus,
         errorIndex, varBinds) = cmdgen.CommandGenerator().getCmd(
            self.SecurityDataReadOnly,
            self.UdpTransportTarget,
            snmpRequest,
            lookupMib=False)

        # Predefine our results list
        results = []

        if errorIndication:
            raise SnmpError(errorIndication, function_name)
        else:
            if errorStatus:
                raise SnmpError('%s at %s\n' %
                                (errorStatus.prettyPrint(),
                                 errorIndex and varBinds[int(errorIndex) - 1] or '?'), function_name)
            else:
                for name, val in varBinds:
                    results.append(val)

        return results

    #@abstractmethod
    def GetNext(self, oid):
        """
        :param oid: Snmp Object Id
        :type oid: tuple
        :return: Query result list
        """
        function_name = self.GetNext.__name__

        (errorIndication, errorStatus,
         errorIndex, varBinds) = cmdgen.CommandGenerator().nextCmd(
            self.SecurityDataReadOnly,
            self.UdpTransportTarget,
            oid,
            lookupMib=False)

        # Predefine our results list
        results = []

        if errorIndication:
            raise SnmpError(errorIndication, function_name)
        else:
            if errorStatus:
                raise SnmpError('%s at %s\n' %
                                (errorStatus.prettyPrint(),
                                 errorIndex and varBinds[int(errorIndex) - 1] or '?'), function_name)
            else:
                for varBindTableRow in varBinds:
                    for name, val in varBindTableRow:
                        results.append('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

        return results

    #@abstractmethod
    def Set(self, oid, val, SnmpValType=None):
        """
        :param oid: Object ID
        :type oid: tuple
        :param val: Value to be set
        :param SnmpValType: SNMP value type
        :return:
        """
        function_name = self.Set.__name__

        # retrive snmp data type
        snmpData = NativeVal2Snmp(val, SnmpValType)
        snmpSetTuple = (oid, snmpData)
        errorIndication, errorStatus, \
        errorIndex, varBinds = cmdgen.CommandGenerator().setCmd(
            self.SecurityDataReadWrite,
            self.UdpTransportTarget,
            snmpSetTuple)
        if errorIndication:
            raise SnmpError(errorIndication, function_name)
        else:
            if errorStatus:
                raise SnmpError('%s at %s\n' %
                          (errorStatus.prettyPrint(),
                           errorIndex and varBinds[int(errorIndex) - 1] or '?'), function_name)
            else:
                for name, val in varBinds:
                    if name == oid:
                        return str(val).split()


class SNMPv1v2c(SnmpBasic):
    def __init__(self, snmp_version=SnmpProtocolVersion.v2):
        super(SNMPv1v2c, self).__init__()
        self.SnmpVersion = snmp_version

    @property
    def SnmpVersion(self):
        return self._snmp_version

    @SnmpVersion.setter
    def SnmpVersion(self, snmp_version):
        if isinstance(snmp_version, SnmpProtocolVersion):
            self._snmp_version = snmp_version
        elif isinstance(snmp_version, int) and snmp_version in SnmpProtocolVersion.__members__:
            self._snmp_version = SnmpProtocolVersion(snmp_version)

    def __call__(self, ip_addr, read_write_community='private', read_only_community='public', port_id = 161, timeout_val = 2, retries_num = 3):
        """
        :param ip_addr: Hostname or Ip address string
        :type ip_addr: str
        :param read_write_community: Community with Read and Write permissions
        :type read_write_community: str
        :param read_only_community: Community with Read Only permissions
        :type read_only_community: str
        :param port_id: L4 port number
        :type port_id: int
        :param timeout_val: Response timeout in seconds
        :type timeout_val: int
        :param retries_num: Maximum number of request retries, 0 retries means just a single request.
        :type retries_num: int
        """
        self.SetTrasnportLayerParams(ip_addr, port_id, timeout_val, retries_num)
        self.SetSecurityData(read_write_community, read_only_community)

    def SetSecurityData(self, read_write_community='private', read_only_community='public'):
        """
        The Community Data is used for configuring Community-Based Security Model of SNMPv1/SNMPv2c
        :param read_write_community: Community with Read and Write permissions
        :type read_write_community: str
        :param read_only_community: Community with Read Only permissions
        :type read_only_community: str
        """
        function_name = self.SetSecurityData.__name__
        try:
            strVal = str(read_write_community)
            if not strVal: #if string is empty
                raise Exception
            else:
                self.InputParams.ReadWriteCommunity = strVal
        except:
            raise ArgumentError("Illegal community value: " + read_write_community + ". Should be a non-empty string",
                                function_name)

        try:
            strVal = str(read_only_community)
            if read_only_community is not None and strVal:
                self.InputParams.ReadOnlyCommunity = strVal
            else:
                raise Exception
        except:
            # if read only community is illegal use read write community instead
            self.InputParams.ReadOnlyCommunity = self.InputParams.ReadWriteCommunity

        # setting Security Data with SNMP Comminuty configuration
        mp_model = 0 if self.SnmpVersion == SnmpProtocolVersion.v1 else 1
        self.SecurityDataReadWrite = cmdgen.CommunityData(self.InputParams.ReadWriteCommunity, mpModel=mp_model)
        self.SecurityDataReadOnly = cmdgen.CommunityData(self.InputParams.ReadOnlyCommunity, mpModel=mp_model)


class SNMPv3(SnmpBasic):
    def __init__(self):
        super(SNMPv3, self).__init__()


    def SetSecurityData(self, user_name_rw, auth_key_rw=None, priv_key_rw=None,
                        auth_protocol_rw=USMAuthProtocol.usm_NoAuth, priv_protocol_rw=USMPrivProtocol.usm_NoPriv,
                        user_name_ro=None, auth_key_ro=None, priv_key_ro=None,
                        auth_protocol_ro=USMAuthProtocol.usm_NoAuth, priv_protocol_ro=USMPrivProtocol.usm_NoPriv):
        """
        A method configures the SNMPv3 Security User Based parameters.
        The arguments followed by rw represent the Read Write arguments with SNMPv3 Read Write permission,
        when ro - Read Only.
        I.e. user_name_rw - username with SNMPv3 Read Write permissions
        If read only username (user_name_ro) argument is None, the function will ser a Read Write user parameters for
        Read Only operations.
        For more details please visit the PySnmp Security Parameters tutorial page:
        http://snmplabs.com/pysnmp/docs/api-reference.html#security-parameters
        :param user_name_rw: A human readable string representing the name of the SNMP USM user (Read Write)
        :type user_name_rw: str
        :param auth_key_rw: Initial value of the secret authentication key (Read Write)
        :type auth_key_rw: str
        :param priv_key_rw: Initial value of the secret encryption key (Read Write)
        :type priv_key_rw: str
        :param auth_protocol_rw: The type of authentication protocol which is used. Default - usmNoAuthProtocol.
        :type auth_protocol_rw: USMAuthProtocol
        :param priv_protocol_rw: The type of encryption protocol which is used. Default - usmNoPrivProtocol.
        :type priv_protocol_rw: USMPrivProtocol
        :param user_name_ro: A human readable string representing the name of the SNMP USM user (Read Only),
        if not specified all the arguments related to read only user will be copied from Read Write user.
        :type user_name_ro: str
        :param auth_key_ro: Initial value of the secret authentication key (Read Only)
        :type auth_key_ro: str
        :param priv_key_ro: Initial value of the secret encryption key (Read Only)
        :type priv_key_ro: str
        :param auth_protocol_ro: The type of authentication protocol which is used (Read Only)
        :type auth_protocol_ro: USMAuthProtocol
        :param priv_protocol_ro: Initial value of the secret encryption key (Read Only)
        :type priv_protocol_ro: USMPrivProtocol
        """

        function_name = self.SetSecurityData.__name__

        # Read write values
        if isinstance(user_name_rw, str):
            if not user_name_rw:  # if string is empty
                raise ArgumentError("Illegal username rw value: " + user_name_rw + " Should be a non-empty string",
                                    function_name)
            else:
                self.InputParams.ReadWrite_UserName = user_name_rw
        else:
            raise ArgumentError("Illegal username rw value. Should be a non-empty string",
                                function_name)

        if not auth_key_rw:  # if string is empty
            self.InputParams.ReadWrite_AuthKey = None
        else:
            self.InputParams.ReadWrite_AuthKey = auth_key_rw

        if not priv_key_rw:  # if string is empty
            self.InputParams.ReadWrite_PrivKey = None
        else:
            self.InputParams.ReadWrite_PrivKey = priv_key_rw

        #if auth_protocol_rw in AuthProtocol.__members__:
            #print "OK"
        #else:
            #print "not ok"

        if USMAuthProtocol.HasMember(auth_protocol_rw):
            self.InputParams.ReadWrite_AuthProtocol = auth_protocol_rw
        else:
            raise ArgumentError("Illegal Authentication Protocol rw value. Should be of type USMAuthProtocol.",
                                function_name)

        if USMPrivProtocol.HasMember(priv_protocol_rw):
            self.InputParams.ReadWrite_PrivProtocol = priv_protocol_rw
        else:
            raise ArgumentError("Illegal Privacy Protocol rw value. Should be of type USMPrivProtocol.",
                                function_name)

        # Read Only values
        if user_name_ro is None:  # if read only username value was not set
            self.InputParams.ReadOnly_UserName = self.InputParams.ReadWrite_UserName
            self.InputParams.ReadOnly_AuthKey = self.InputParams.ReadWrite_AuthKey
            self.InputParams.ReadOnly_PrivKey = self.InputParams.ReadWrite_PrivKey
            self.InputParams.ReadOnly_AuthProtocol = self.InputParams.ReadWrite_AuthProtocol
            self.InputParams.ReadOnly_PrivProtocol = self.InputParams.ReadWrite_PrivProtocol
        else:
            if isinstance(user_name_ro, str):
                if not user_name_ro:  # if string is empty
                    raise ArgumentError("Illegal username ro value: " + user_name_ro + " Should be a non-empty string",
                                        function_name)
                else:
                    self.InputParams.ReadOnly_UserName = user_name_ro
            else:
                raise ArgumentError("Illegal username ro value. Should be a non-empty string",
                                    function_name)
            if not auth_key_ro:  # if string is empty
                self.InputParams.ReadOnly_AuthKey = None
            else:
                self.InputParams.ReadOnly_AuthKey = auth_key_ro

            if not priv_key_ro:  # if string is empty
                self.InputParams.ReadOnly_PrivProtocol = None
            else:
                self.InputParams.ReadOnly_PrivProtocol = priv_key_ro

            if USMAuthProtocol.HasMember(auth_protocol_ro):
                self.InputParams.ReadOnly_AuthProtocol = auth_protocol_ro
            else:
                raise ArgumentError("Illegal Authentication Protocol ro value. Should be of type USMAuthProtocol.",
                                    function_name)

            if USMPrivProtocol.HasMember(priv_protocol_ro):
                self.InputParams.ReadOnly_PrivProtocol = priv_protocol_ro
            else:
                raise ArgumentError("Illegal Privacy Protocol ro value. Should be of type USMPrivProtocol.",
                                    function_name)

        # setting Security Data with SNMPv3 User Based configuration
        self.SecurityDataReadWrite = cmdgen.UsmUserData(self.InputParams.ReadWrite_UserName,
                                                        self.InputParams.ReadWrite_AuthKey,
                                                        self.InputParams.ReadWrite_PrivKey,
                                                        SnmpV3AuthProtocolMap[self.InputParams.ReadWrite_AuthProtocol],
                                                        SnmpV3PrivProtocolMap[self.InputParams.ReadWrite_PrivProtocol])
        self.SecurityDataReadOnly = cmdgen.UsmUserData(self.InputParams.ReadOnly_UserName,
                                                       self.InputParams.ReadOnly_AuthKey,
                                                       self.InputParams.ReadOnly_PrivKey,
                                                       SnmpV3AuthProtocolMap[self.InputParams.ReadOnly_AuthProtocol],
                                                       SnmpV3PrivProtocolMap[self.InputParams.ReadOnly_PrivProtocol])