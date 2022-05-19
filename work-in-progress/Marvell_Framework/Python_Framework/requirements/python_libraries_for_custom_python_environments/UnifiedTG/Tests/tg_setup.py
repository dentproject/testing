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
from UnifiedTG.Unified.UTG import utg
from UnifiedTG.Unified.Port import Port
from pprint import pprint
import time
from datetime import datetime
import unittest
import pytest


simple_debug = False
Statistics_suite = True
Trigger_Suite =     True
FlowControl_Suite = True
Vlan_Suite =        True
L1_Suite =          True
Capture_Suite =     True
Known_Issues =      True
Streams_Suite =     True
Packet_Headers =    True
Ports_Suite =       True
Packet_Builder    = True
Protocol_Management_Suite = True


userLogin = "OlegK"
serverHostLT512 = "pt-lt0512"
serverHost2 = "il-wtsvs01"
ptgen5 = "pt-vcgen5"
chasIx1 = "10.5.224.86"
chasIx2 = "10.5.224.94"
mGigChassis = "10.5.224.81"
pName1 = "tgPort"
pName2 = "my_port2"
pName3 = "tgPort3"
pName4 = "my_port4"
uriP1 = chasIx1 + "/15/1"
uriP2 = chasIx1 + "/15/2"
uriP3 = chasIx1 + "/15/3"
uriP4 = chasIx1 + "/15/4"
uriHD1 = chasIx2 + "/4/1"
uriHD103 = chasIx2 + "/10/3"
uriHD47 = chasIx2 + "/4/7"
uriHD6 = chasIx2 + "/4/6"
uriHD40 = chasIx2 + "/1/1"
uriHD69 = chasIx2 + "/6/9"
mGigUri = mGigChassis+"/1/13"
#portsList = [pName1 + ":" + uriHD1]

Nic1 = 'lb/0/0'
Nic2 = 'lb/0/1'
Nic3 = '0/0/2'
Nic4 = '0/0/3'

#vendorType = 'Ostinato'
#vendorType = 'Ixia'
vendorType = 'ixiassh'
#vendorType = 'Xena'


loopBackMode = False
rxSleep = 2
offset_adapter = 2
if vendorType == 'Ostinato':
    serverHost1 = '127.0.0.1'  #'10.28.132.214' #serverHostLT512 =  '10.5.80.12'
    #portsList = [pName1 + ":" + Nic1,pName2 + ":" + Nic2] #
    portsList = [pName1 + ":" + Nic3, pName2 + ":" + Nic4]  #
    loopBackMode = False
    rxSleep = 3
    FlowControl_Suite = False
    Vlan_Suite = False
    L1_Suite = False
    Packet_Builder = False
    Statistics_suite = False
elif vendorType == 'Ixia':

    pass
    serverHost1 = '10.5.224.94'
    chas = serverHost1
    # p1 = chas + '/3/25'
    # # p2 = chas + '/6/20'
    #p1 = chas + '/9/1'
    p1 = chas + '/6/11'

    # serverHost1 = serverHost2
    # chas = '10.5.224.86'
    # p1 = chas + '/15/1'
    # p2 = chas + '/15/2'
    # portsList = [p1 + ":" + p1, p2 + ":" + p2] #

    portsList = [p1 + ":" + p1]
    loopBackMode = True



elif vendorType == 'ixiassh':

    chas = serverHost1 =  '10.5.238.181' #T400
    serverHost2 = chas
    p1 = chas + '/1/5'
    #p2 = chas + '/1/8'

    # serverHost1 = '10.5.40.181' #= serverHost2
    # chas = serverHost1
    # p1 = chas + '/1/8'
    #p2 = chas + '/1/8'
    #portsList = [p1 + ":" + p1,p2 + ":" + p2]

    # serverHost1 = '10.5.225.194' #'10.5.226.136'#'10.5.238.182'
    # chas = '10.5.225.194' #serverHost1
    # p1 = chas + '/11/10'
    # p2 = chas + '/11/11'
    # portsList = [p1 + ":" + p1,p2 + ":" + p2]

    portsList = [p1 + ":" + p1]
    loopBackMode = True


elif vendorType == 'Xena':
    loopBackMode = True
    offset_adapter = 0
    #,pName2+":"+mGigUri
    #pName1+":" + uriHD1
    #, pName2 + ":" + mGigUri
    serverHost1 = '10.4.91.101'
    uriHD1 = '10.4.91.101/4/0'
    portsList = [pName1+":" + uriHD1]
    #portsList = [pName1 + ":" + mGigUri]
    #portsList = [uriP4+":"+uriP4]
    #portsList = [uriHD43 + ":" + uriHD43]
    #portsList = [uriP1 + ":" + uriP1]
    #portsList = [uriHD47 + ":" + uriHD47]
    #portsList = [uriHD103 + ":" + uriHD103]



