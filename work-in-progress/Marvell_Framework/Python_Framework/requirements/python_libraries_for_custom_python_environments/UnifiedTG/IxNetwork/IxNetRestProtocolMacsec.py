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


from IxNetRestApi.IxNetRestApiProtocol import Protocol

class IxNetRestProtocolMacsec(Protocol):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
    # def __init__(self,ixnObj):
    #     super(self.__class__, self).__init__(ixnObj)



    def configMacSecNgpf(self, obj=None, port=None, portName=None, ngpfEndpointName=None, **kwargs):
        """
        Description
            Create or modify NGPF IPv4.
            To create a new IPv4 stack in NGPF, pass in the Ethernet object.
            If modifying, there are four options. 2-4 will query for the IP object handle.

               1> Provide the IPv4 object handle using the obj parameter.
               2> Set port: The physical port.
               3> Set portName: The vport port name.
               4> Set NGPF IP name that you configured.

        Parameters
            obj: <str>: None or Ethernet obj: '/api/v1/sessions/1/ixnetwork/topology/1/deviceGroup/1/ethernet/1'
                                IPv4 obj: '/api/v1/sessions/1/ixnetwork/topology/1/deviceGroup/1/ethernet/1/ipv4/1'

            port: <list>: Format: [ixChassisIp, str(cardNumber), str(portNumber)]
            portName: <str>: The virtual port name.
            ngpfEndpointName: <str>: The name that you configured for the NGPF IPv4 endpoint.

            kwargs:
               ipv4AddressMultivalueType & gatewayMultivalueType:
                                    Default='counter'. Options: alternate, custom, customDistributed, random, repeatableRandom,
                                                                repeatableRandomRange, valueList
                                    To get the multivalue settings, refer to the API browser.

               ipv4Address: <dict>: {'start': '100.1.1.100', 'direction': 'increment', 'step': '0.0.0.1'},
               ipv4AddressPortStep: <str>|<dict>:  disable|0.0.0.1
                                    Incrementing the IP address on each port based on your input.
                                    0.0.0.1 means to increment the last octet on each port.

               gateway: <dict>: {'start': '100.1.1.1', 'direction': 'increment', 'step': '0.0.0.1'},
               gatewayPortStep:  <str>|<dict>:  disable|0.0.0.1
                                 Incrementing the IP address on each port based on your input.
                                 0.0.0.1 means to increment the last octet on each port.

               prefix: <int>:  Example: 24
               rsolveGateway: <bool>

        Syntax
            POST:  /api/v1/sessions/{id}/ixnetwork/topology/{id}/deviceGroup/{id}/ethernet/{id}/ipv4
            PATCH: /api/v1/sessions/{id}/ixnetwork/topology/{id}/deviceGroup/{id}/ethernet/{id}/ipv4/{id}

        Example to create a new IPv4 object:
             ipv4Obj1 = createIpv4Ngpf(ethernetObj1,
                                       ipv4Address={'start': '100.1.1.1', 'direction': 'increment', 'step': '0.0.0.1'},
                                       ipv4AddressPortStep='disabled',
                                       gateway={'start': '100.1.1.100', 'direction': 'increment', 'step': '0.0.0.0'},
                                       gatewayPortStep='disabled',
                                       prefix=24,
                                       resolveGateway=True)

        Return
            /api/v1/sessions/{id}/ixnetwork/topology/{id}/deviceGroup/{id}/ethernet/{id}/ipv4/{id}
        """
        createNewMacSecObj = True
        protoName = 'staticMacsec'


        if obj is not None:
            if protoName in obj:
                # To modify macsec
                macSecObj = obj
                createNewMacSecObj = False
            else:
                # To create a new macsec object
                macSecUrl = self.ixnObj.httpHeader+obj+'/'+protoName

                self.ixnObj.logInfo('Creating new macsec in NGPF')
                response = self.ixnObj.post(macSecUrl)
                macSecObj = response.json()['links'][0]['href']

        # To modify
        if ngpfEndpointName:
            macSecObj = self.getNgpfObjectHandleByName(ngpfEndpointName=ngpfEndpointName, ngpfEndpointObject=protoName)
            createNewMacSecObj = False

        # To modify
        if port:
            x = self.getProtocolListByPortNgpf(port=port)
            macSecObj = self.getProtocolObjFromProtocolList(x['deviceGroup'], protoName)[0]
            createNewMacSecObj = False

        # To modify
        if portName:
            x = self.getProtocolListByPortNgpf(portName=portName)
            macSecObj = self.getProtocolObjFromProtocolList(x['deviceGroup'], protoName)[0]
            createNewMacSecObj = False

        macSecResponse = self.ixnObj.get(self.ixnObj.httpHeader+macSecObj)

        if 'name' in kwargs:
            self.ixnObj.patch(self.ixnObj.httpHeader+macSecObj, data={'name': kwargs['name']})

        if 'multiplier' in kwargs:
            self.configDeviceGroupMultiplier(objectHandle=macSecObj, multiplier=kwargs['multiplier'], applyOnTheFly=False)


        if 'dutMac' in kwargs:
            multivalue = macSecResponse.json()['dutMac']
            self.ixnObj.logInfo('Configure MAC address. Attribute for multivalueId = jsonResponse["mac"]')

            # Default to counter
            multivalueType = 'counter'

            if 'macAddressMultivalueType' in kwargs:
                multivalueType = kwargs['macAddressMultivalueType']

            if multivalueType == 'random':
                self.ixnObj.patch(self.ixnObj.httpHeader+multivalue, data={'pattern': 'random'})
            else:
                self.configMultivalue(multivalue, multivalueType, data=kwargs['dutMac'])

            # Config Mac Address Port Step
            if 'macAddressPortStep' in kwargs:
                self.ixnObj.logInfo('Configure MAC address port step')
                portStepMultivalue = self.ixnObj.httpHeader + multivalue+'/nest/1'
                if 'macAddressPortStep' in kwargs:
                    if kwargs['macAddressPortStep'] != 'disabled':
                        self.ixnObj.patch(portStepMultivalue, data={'step': kwargs['macAddressPortStep']})
                    if kwargs['macAddressPortStep'] == 'disabled':
                        self.ixnObj.patch(portStepMultivalue, data={'enabled': False})



        if createNewMacSecObj == True:
            self.configuredProtocols.append(macSecObj)

        return macSecObj
