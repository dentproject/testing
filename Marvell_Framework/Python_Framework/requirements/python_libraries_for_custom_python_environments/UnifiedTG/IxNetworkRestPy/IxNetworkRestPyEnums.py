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

from UnifiedTG.Unified.TGEnums import TGEnums


class ixNetworkRestPyEnums(object):
    from enum import Enum

    class Traffic_Type(Enum):
        Raw = 'raw'
        Ethernet = 'ethernetVlan'
        Ipv4 = 'ipv4'
        Ipv6 = 'ipv6'
        ipv4Application = 'ipv4ApplicationTraffic'
        ipv6Application = 'ipv6ApplicationTraffic'

    class Encryption_Engine(Enum):
        HW = 'hardwareBased'
        SW = 'softwareBased'

    class Cipher_Suite(Enum):
        AES128 = 'aes128'
        AES256 = 'aes256'

    class ProtocolType(Enum):
        eth = '^ethernet$'
        #macsec = '^eth$'
        vlan ='^vlan$'
        ipv4 = '^ipv4$'
        udp = '^udp$'
        custom = '^custom$'

    class AppLib_ObjectiveType(Enum):
        simulatedUsers = 'simulatedUsers'
        throughputGbps = 'throughputGbps'
        throughputKbps = 'throughputKbps'
        throughputMbps = 'throughputMbps'


    class MacSec_Stats_Name(Enum):
        Port = 'Port'
        SessionsUp = 'Sessions Up'
        SessionsDown = 'Sessions Down'
        SessionsNotStarted = 'Sessions Not Started'
        SessionsTotal = 'Sessions Total'
        ProtectedPacketTx = 'Protected Packet Tx'
        EncryptedPacketTx = 'Encrypted Packet Tx'
        ValidPacketRx = 'Valid Packet Rx'
        BadPacketRx = 'Bad Packet Rx'
        BadTag_ICV_Discarded = 'Bad Tag/ICV Discarded'
        OutofWindowDiscarded = 'Out of Window Discarded'
        UnknownSCIDiscarded = 'Unknown SCI Discarded'
        UnusedSADiscarded = 'Unused SA Discarded'
        InvalidICVDiscarded = 'Invalid ICV Discarded'
        UnknownSCIRx = 'Unknown SCI Rx'
        UnusedSARx = 'Unused SA Rx'
        InvalidICVRx = 'Invalid ICV Rx'
        TxBytesProtected = 'Tx Bytes Protected'
        TxBytesEncrypted = 'Tx Bytes Encrypted'
        RxBytesValidated = 'Rx Bytes Validated'
        RxBytesDecrypted = 'Rx Bytes Decrypted'
        NonMACsecPacketRx = 'Non-MACsec Packet Rx'

