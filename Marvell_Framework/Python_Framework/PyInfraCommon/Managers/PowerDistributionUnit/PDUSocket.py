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
from builtins import str
from builtins import range
from builtins import object
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
import logging
import os
import os.path
import socket
from abc import ABCMeta, abstractmethod
import re

from PyInfraCommon.GlobalFunctions.Utils.Exception import GetStackTraceOnException
from PyInfraCommon.GlobalFunctions.Utils.Function import GetFunctionName
from .errorHandlers import PDUError, PDUArgumentError, PDUEnvironmentError
from PyInfraCommon.Managers.SNMP.SNMPTools import *
from enum import IntEnum
from PyInfraCommon.Globals.Logger.GlobalTestLogger import GlobalLogger

# PDU type
class PduVendorType(IntEnum):
    Unknown = 0
    APC = 1
    Sentry = 2
    Raritan = 3

    @classmethod
    def HasMember(cls, member):
        return (any(member == item.value for item in cls))

# Outlet Action type
class OutletActionType(object):
    On, Off, Reboot = list(range(3))

# Connection method
class ConnectionMethod(object):
    Unknown, Serial, Telnet, SSH, SNMP = list(range(5))

# PDU Socket abstract base class
class PduSocket(object):
    # __metaclass__ = ABCMeta

    def __init__(self, socket_id, pdu_type):
        self.SocketId = socket_id
        self.PduType = pdu_type
        self._Logger = None


    def __call__(self, action=None):
        if action != None:
            if action == OutletActionType.On:
                self.on()
            elif action == OutletActionType.Off:
                self.off()
            elif action == OutletActionType.Reboot:
                self.reboot()

        return self.status()

    @property
    def Logger(self):
        return self._Logger

    @Logger.setter
    def Logger(self, logObj):
        self._Logger = logObj

    @property
    def SocketId(self):
        return self._SocketId


    @SocketId.setter
    def SocketId(self, value):
        """
           :param value: Power socket identifier. If
           :type value: str | int
           """
        if isinstance(value, int) or isinstance(value, str):
            self._SocketId = value
        else:
            raise PDUArgumentError("Wrong socket id value. Should be a string or integer!",'SocketId setter')


    @property
    def PduType(self):
        return self._PduType


    @PduType.setter
    def PduType(self, value):
        """
           :param value: Power Distribution Unit type
           :type value: PduType
           """
        #function_name = self.PduType.__name__
        if PduVendorType.HasMember(value):
            self._PduType = value
        else:
            raise PDUArgumentError("Wrong PduType argument. Should be legal value from PduVendorType type!",
                                   'PduType setter')


    @abstractmethod
    def on(self):
        pass


    @abstractmethod
    def off(self):
        pass


    @abstractmethod
    def reboot(self):
        pass


    @abstractmethod
    def status(self):
        pass


# PDU Socket SNMP class inherited from abstract PduOutlet
class PduSocket_SNMP(PduSocket):

    class PduSNMPParams(object):
        def __init__(self):
            self.socketName = None
            self.setSocketStates = {}
            self.getSocketStates = {}

            self.socketControlOID = None
            self.socketNameOID = None
            self.socketStatusOID = None


    def __init__(self, snmp_obj, socket_id, pdu_type=PduVendorType.Unknown):
        super(self.__class__, self).__init__(socket_id, pdu_type)
        self.SNMP = snmp_obj
        self.__pduParams = self.PduSNMPParams()
        if self.PduType == PduVendorType.Unknown:
            #try to auto-detect the PDU type
            self.PduType = self.getPduType()
            if self.PduType == PduVendorType.Unknown:
                raise PDUEnvironmentError("Unknown PDU type. Type not specified and failed to be auto-detected!",
                                          'PduOutlet_SNMP.init')
        self.setSocketParams()


    @property
    def SNMP(self):
        return self._SNMP


    @SNMP.setter
    def SNMP(self, value):
        """
        :param value: Snmp object
        :type value: SNMPv1v2c | SNMPv3
        """
        #function_name = self.SNMP.__name__
        if not isinstance(value, SnmpBasic):
            raise PDUArgumentError("Wrong argument value. Should be a SNMP object!", "SNMP member setter")
        else:
            self._SNMP = value


    def setSocketParams(self):
        function_name = self.setSocketParams.__name__
        if self._SNMP is None:
            raise PDUEnvironmentError('Illegal method sequence call. Set SNMP object previously.', function_name)
        else:

            ########## APC ##########
            if  self.PduType == PduVendorType.APC:
                # OID: sPDUOutletCtl (outletControlOID)
                # Setting this variable to outletOn (1) will turn the outlet on.
                # Setting this variable to outletOff (2) will turn the outlet off.
                # Setting this variable to outletReboot (3) will reboot the outlet.
                # Setting this variable to outletOnWithDelay (5) will turn the outlet on after the sPDUOutletPowerOnTime OID has elapsed.
                # This option is not valid for MasterSwitch firmware version 1.X.
                # Setting this variable to outletOffWithDelay (6) will turn the outlet off after the sPDUOutletPowerOffTime OID has elapsed.
                # This option is not valid for MasterSwitch firmware version 1.X.
                # Setting this variable to outletRebootWithDelay (7) will turn the outlet off after the sPDUOutletPowerOffTime OID has elapsed,
                # wait the sPDUOutletRebootDuration OID time, then turn the outlet back on.
                # This option is not valid for MasterSwitch firmware version 1.X.
                #self.__pduParams.socketControlOID = (1, 3, 6, 1, 4, 1, 318, 1, 1, 4, 4, 2, 1, 3)
                self.__pduParams.socketControlOID = (1, 3, 6, 1, 4, 1, 318, 1, 1, 12, 3, 3, 1, 1,4)
                self.__pduParams.setSocketStates = {'On': 1, 'Off': 2, 'Reboot': 3}
                self.__pduParams.getSocketStates = {1: 'On', 2:'Off'}
                # OID: rPDUOutletStatusOutletName
                # The name of the outlet. Maximum size is dependent on device. An error will be returned if the set request exceeds the max size.
                # This OID is provided for informational purposes only.
                self.__pduParams.socketNameOID = (1, 3, 6, 1, 4, 1, 318, 1, 1, 12, 3, 5, 1, 1, 2)
                # OID: sPDUOutletCtl (outletStatusOID)
                # Getting this variable will return the outlet state. If the outlet is on, the outletOn (1) value will be returned.
                # If the outlet is off, the outletOff (2) value will be returned.
                # If the state of the outlet cannot be determined, the outletUnknown (4) value will be returned.
                self.__pduParams.outletStatusOID =  (1, 3, 6, 1, 4, 1, 318, 1, 1, 12, 3, 5, 1, 1,4)
                self.__pduParams.socketStatusOID = self.__pduParams.outletStatusOID
            ########## Sentry ##########
            elif  self.PduType == PduVendorType.Sentry:
                self.__pduParams.socketControlOID = (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 11, 1, 1)
                self.__pduParams.setSocketStates = {'On': 1, 'Off': 2, 'Reboot': 3}
                self.__pduParams.getSocketStates = {0: 'off', 1: 'on', 2: 'offWait', 3: 'onWait', 4: 'offError',
                                                    5: 'onError', 6: 'noComm', 7: 'reading', 8: 'offFuse', 9: 'onFuse'}
                # outletName OBJECT-TYPE
                # SYNTAX      DisplayString(SIZE(0..24)
                # MAX-ACCESS  read-write
                # STATUS      current
                # DESCRIPTION
                #           "The name of the outlet."
                self.__pduParams.socketNameOID = (1, 3, 6, 1, 4, 1 , 1718, 3, 2, 3, 1, 3, 1, 1)
                # outletStatus OBJECT-TYPE
                # SYNTAX      INTEGER {
                #             off(0),
                #             on(1),
                #             offWait(2),
                #             onWait(3),
                #             offError(4),
                #             onError(5),
                #             noComm(6),
                #             reading(7),
                #             offFuse(8),
                #             onFuse(9)
                #
                # MAX-ACCESS  read-only
                # STATUS      current
                # DESCRIPTION
                #       "The status of the outlet.  If the outletCapabilities
                #       'onSense' bit is TRUE, then the state indicates the sensed
                #       state of the outlet, not a derived state, and 'offError'
                #       and 'onError' are supported to indicate a mismatch between
                # the control and sensed state.  If the outletCapabilities
                # 'fusedBranch' bit is TRUE, then the outlet is on a fused
                # branch circuit that can detect the fuse state, and 'offFuse'
                # and 'onFuse' are supported to indicate a fuse error."

                self.__pduParams.socketStatusOID = (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 5, 1, 1)
            elif self.PduType is PduVendorType.Raritan:
                self.__pduParams.socketControlOID = (1,3,6,1,4,1,13742,6,4,1,2,1,2,1)
                self.__pduParams.setSocketStates = {'On': 1, 'Off': 0, 'Reboot': 2}
                self.__pduParams.getSocketStates = {7: 'On', 8:'Off'}
                # OID: rPDUOutletStatusOutletName
                # The name of the outlet. Maximum size is dependent on device. An error will be returned if the set request exceeds the max size.
                # This OID is provided for informational purposes only.
                self.__pduParams.socketNameOID = (1,3,6,1,4,1,13742,6,3,5,3,1,3,1)
                # OID: sPDUOutletCtl (outletStatusOID)
                # Getting this variable will return the outlet state. If the outlet is on, the outletOn (1) value will be returned.
                # If the outlet is off, the outletOff (2) value will be returned.
                # If the state of the outlet cannot be determined, the outletUnknown (4) value will be returned.
                self.__pduParams.outletStatusOID =  (1,3,6,1,4,1,13742,6,4,1,2,1,3,1)
                self.__pduParams.socketStatusOID = self.__pduParams.outletStatusOID
            else:
                raise PDUEnvironmentError('Error setting outlet base OID. Unknwon PDU type!', function_name)

            self.__pduParams.socketName = self.getSocketName()

    def getPduType(self):
        result = PduVendorType.Unknown
        # System Description oid
        testOid = (('SNMPv2-MIB', 'sysDescr'), 0)
        try:
            getResults = self.SNMP.Get(testOid)
        except Exception as e:
            GlobalLogger.logger.error('Failed to auto-detect the PDU socket type.\nError: {}'.format(GetStackTraceOnException(e)))
            pass
            #print 'Failed to auto-detect the PDU socket type. Initiator: {}\nError: {}'.format(str(e), e.initiator)

        regexApc = r"APC"
        regexSentry = r"Sentry"
        regexRaritan = r"PX"
        for val in getResults:
            prettyVal = val.prettyPrint()
            if re.match(regexApc, prettyVal, re.I) is not None:
                result = PduVendorType.APC
                break
            elif re.match(regexSentry, prettyVal, re.I) is not None:
                result = PduVendorType.Sentry
                break
            elif re.match(regexRaritan, prettyVal, re.I) is not None:
                result = PduVendorType.Raritan
                break
        return result

    def getSocketName(self):
        try:
            snmpResults = self.SNMP.Get(self.__pduParams.socketNameOID + (self.SocketId,))
        except SNMPToolError as e:
            GlobalLogger.logger.info('Failed to get the PDU socket name. Initiator: {}\nError: {}'.format(e,
                                                                                                          e.initiator))
            #print 'Failed to get the PDU socket name. Initiator: {}\nError: {}'.format(str(e), e.initiator)

        socket_name = SnmpVal2Native(snmpResults[0])
        if socket_name == None:
            self.__pduParams.socketName = 'Socket' + str(self.SocketId)
        return socket_name

    def on(self):
        # logging.info("Action \'ON\' requested for " + self.__pduParams.outletName +
        #              " on outlet # " + str(self.SocketId))
        funcname = GetFunctionName(self.on)
        GlobalLogger.logger.debug(funcname+"Action \'ON\' requested for PDU " + self.SNMP.InputParams.ip +
                                   " socket#" + str(self.SocketId) + " ("
               + self.__pduParams.socketName + ")" + os.linesep)
        try:
            self.SNMP.Set(self.__pduParams.socketControlOID + (self.SocketId,),
                         self.__pduParams.setSocketStates['On'])
            return self.status()
        except SNMPToolError as e:
            GlobalLogger.logger.info('Failed to \'On\' the PDU socket. Initiator: {}\nError: {}'.format(str(e),
                                                                                                        e.initiator))
            #print 'Failed to \'On\' the PDU socket. Initiator: {}\nError: {}'.format(str(e), e.initiator)

    def off(self):
        funcname = GetFunctionName(self.off)
        GlobalLogger.logger.debug(funcname+"Action \'Off\' requested for PDU " + self.SNMP.InputParams.ip +
               " socket#" + str(self.SocketId) + " ("
               + self.__pduParams.socketName + ")" + os.linesep)
        try:
            self.SNMP.Set(self.__pduParams.socketControlOID + (self.SocketId,),
                         self.__pduParams.setSocketStates['Off'])
            return self.status()
        except SNMPToolError as e:
            GlobalLogger.logger.info('Failed to \'On\' the PDU socket. Initiator: {}\nError: {}'.format(str(e),
                                                                                                        e.initiator))
            #print 'Failed to \'Off\' the PDU socket. Initiator: {}\nError: {}'.format(str(e), e.initiator)

    def reboot(self):
        funcname = GetFunctionName(self.reboot)
        GlobalLogger.logger.debug(funcname+"Action \'Reboot\' requested for PDU " + self.SNMP.InputParams.ip +
               " socket#" + str(self.SocketId) + " ("
               + self.__pduParams.socketName + ")" + os.linesep)
        try:
            self.SNMP.Set(self.__pduParams.socketControlOID + (self.SocketId,),
                          self.__pduParams.setSocketStates['Reboot'])
            return self.status()
        except SNMPToolError as e:
            GlobalLogger.logger.error('Failed to \'On\' the PDU socket. Initiator: {}\nError: {}'.format(str(e),
                                                                                                        e.initiator))
            #print 'Failed to \'Reboot\' the PDU socket. Initiator: {}\nError: {}'.format(str(e), e.initiator)


    def status(self):
        #print 'status request'
        try:
            snmpResults = self.SNMP.Get(self.__pduParams.socketStatusOID + (self.SocketId,))
        except SNMPToolError as e:
            GlobalLogger.logger.info('Failed to get the PDU socket status. Initiator: {}\nError: {}'.format(
                str(e), e.initiator))
            #print 'Failed to get the PDU socket status. Initiator: {}\nError: {}'.format(str(e), e.initiator)
        #print snmpResults
        outlet_status = SnmpVal2Native(snmpResults[0])
        if outlet_status in self.__pduParams.getSocketStates:
            return self.__pduParams.getSocketStates[outlet_status]
        else:
            raise PDUError('Unrecognized PDU state error')

