# BGP convergence test plan for benchmark performance

- [BGP convergence test plan for benchmark performance](#bgp-convergence-test-plan-for-benchmark-performance)
  - [Overview](#Overview)
    - [Scope](#Scope)
    - [Testbed](#Keysight-Testbed)
  - [Topology](#Topology)
    - [DENT 3 Layer Architecture](#DENT-3-Layer-Architecture)
  - [Setup configuration](#Setup-configuration)
  - [Test methodology](#Test-methodology)
  - [Test cases](#Test-cases)
    - [Test case # 1 – BGP Remote Link Failover Convergence (route withdraw)](#test-case--1--convergence-performance-when-remote-link-fails-route-withdraw)
      - [Test objective](#Test-objective)
      - [Test steps](#Test-steps)
      - [Test results](#Test-results)
      - [Test case](#Test-case)
    - [Test case # 2 – BGP RIB-IN Convergence](#Test-case--2--RIB-IN-Convergence)
      - [Test objective](#Test-objective-1)
      - [Test steps](#Test-steps-1)
      - [Test results](#Test-results-1)
      - [Test case](#Test-case-1)
    - [Test case # 3 - BGP Local Link Failover Convergence](#Test-case--3--Failover-convergence-with-local-link-failure) 
      - [Test objective](#Test-objective-2)
      - [Test steps](#Test-steps-2)
      - [Test results](#Test-results-2)
      - [Test case](#Test-case-2)


## Overview
The purpose of these tests is to test the overall convergence of a IP CLOS network by simulating multiple network devices such as Aggregator/Distributor and using DENT switch DUT as one of the Distributor/Aggregator, closely resembling production environment.

### Scope
These tests are targeted on fully functioning DENT system. The purpose of these tests are to measure convergence when some unexpected failures such as remote link failure, local link failure, node failure or link faults etc occur and some expected failures such as maintenance or upgrade of devices occur in the DENT system.


## Topology

### DENT 3 layer Network [DC] Architecture 

![DENT DUT as Aggregator ](img/Dent-DC.png)


## Setup configuration
We are still discussing about which device to take under test [Aggregator or Distributor or Infra] for optimal results. For current testing we used a DENT "Infra switch" and it is connected to several aggregators and servers which are emulated by IXIA ports. 

IPv4 EBGP neighborship will be configured between DENT DUT and directly connected test ports. Test ports inturn will simulate the  and Leafs by advertising IPv4/IPv6, dual-stack routes.

## Test Methodology
Following test methodologies will be used for measuring convergence. 
* Traffic generator will be used to configure ebgp peering between chassis ports and DENT DUT by advertising IPv4/IPv6, dual-stack routes. 
* Receiving ports will be advertising the same VIP(virtual IP) addresses. 
* Data traffic will be sent from  server to these VIP addresses. 
* Depending on the test case, the faults will be generated. Local link failures can be simulated on the port by "simulating link down" event. 
* Remote link failures can be simulated by withdrawing the routes.
* Control to data plane convergence will be measured by noting down the precise time of the control plane event and the data plane event. Convergence will be measured by taking the difference between contol and data plane events. Traffic generator will create those events and provide us with the control to data plane convergence value under statistics.
* RIB-IN Convergence is the time it takes to install the routes in its RIB and then in its FIB to forward the traffic without any loss. In order to measure RIB-IN convergence, initially IPv4/IPv6 routes will not be advertised. Once traffic is sent, IPv4/IPv6 routes will be advertised and the timestamp will be noted. Once the traffic received rate goes above the configured threshold value, it will note down the data plane above threshold timestamp. The difference between these two event timestamps will provide us with the RIB-IN convergence value.
* Route capacity can be measured by advertising routes in a linear search fashion. By doing this we can figure out the maximum routes a switch can learn and install in its RIB and then in its FIB to forward traffic without any loss.

## Test cases
 We take a subset of the generic topology and used DENT device as an Infra switch. The aggregator switches and the servers are emulated by Ixia ports. We used the same topology for all the below tests.

### Test case # 1 – BGP Remote Link Failover Convergence (route withdraw)
  
#### Test objective
Measure the convergence time when remote link failure event happens with in the network.

<p float="left">
  <img src="img/Single_Link_Failure.png" width="500"  hspace="50"/>
  <img src="img/Failover_convergence.png" width="380" /> 
</p>


#### Test steps
* Configure IPv4 EBGP sessions between Keysight ports and the DENT switch.
* Advertise IPv4 routes along with AS number via configured IPv4 BGP sessions.
* Configure and advertise same IPv4 routes from both the test ports.
* Configure another IPv4 session to send the traffic. This is the server port from which traffic will be sent to the VIP [Virtual IP] addresses.
* Start all protocols and verify that IPv4 BGP neighborship is established.
* Create a data traffic between the server port and receiver ports where the same VIP addresses are configured and enable tracking by "Destination Endpoint" and by "Destination session description".
* Set the desired threshold value for receiving traffic. By default we will be set to 90% of expected receiving rate.
* Apply and start the data traffic.
* Verify that traffic is equally distributed between the receiving ports without any loss.
* Simulate remote link failure by withdrawing the routes from one receiving port. 
* Verify that the traffic is re-balanced and use the other available path to route the traffic.
* Drill down by "Destination Endpoint" under traffic statistics to get the control plane to data plane convergence value.
* In general the convergence value will fall in certain range. In order to achieve proper results, run the test multiple times and average out the test results. 
* Set it back to default configuration.
#### Test results
| Event | Number Of IPv4 Routes  | Convergence (ms)  |
| :---:   | :-: | :-: |
| Withdraw Routes | 1K | 118 |



### Test case # 2 – BGP RIB-IN Convergence 
#### Test objective
Measure the convergence time to install the routes in its RIB and then in its FIB to forward the packets after the routes are advertised.

<p float="left">
  <img src="img/RIB-IN-Convergence_Topology.png" width="500" hspace="50"/>
  <img src="img/RIB-IN_Convergence_graph.png" width="380" /> 
</p>

#### Test steps
* Configure IPv4 EBGP sessions between Keysight ports and the DENT switch.
* Configure IPv4 routes via configured IPv4 BGP sessions. Initially disable the routes so that they don't get advertised after starting the protocols.
* Configure the same IPv4 routes from both the test receiving ports.
* Configure another IPv4 session to send the traffic. This is the server port from which traffic will be sent to the VIP [Virtual IP] addresses.
* Start all protocols and verify that IPv4 BGP neighborship is established.
* Create a data traffic between the server port and receiver ports where the same VIP addresses are configured and enable tracking by "Destination Endpoint" and by "Destination session description".
* Set the desired threshold value for receiving traffic. By default we will be set to 90% of expected receiving rate.
* Apply and start the data traffic.
* Verify that no traffic is being forwarded. 
* Enable/advertise the routes which are already configured. 
* Control plane event timestamp will be noted down and once the receiving traffic rate goes above the configured threshold value, it will note down the data plane threshold timestamp.
* The difference between these two event timestamp will provide us with the RIB-IN convergence time.
* In general the convergence value will fall in certain range. In order to achieve proper results, run the test multiple times and average out the test results. 
* Set it back to default configuration.
#### Test results
| Event | Number Of IPv4 Routes  | Convergence (ms)  |
| :---:   | :-: | :-: |
| Advertise Routes | 1K | 124 |



### Test case # 3 - BGP Local Link Failover Convergence 
#### Test objective
Measure the convergence time when local link failure event happens with in the network.
<p float="left">
  <img src="img/Local_Link_Failure.png" width="500" hspace="50"/>
</p>

#### Test steps
* Configure IPv4 EBGP sessions between Keysight ports and the DENT switch.
* Advertise IPv4 routes along with AS number via configured IPv4 BGP sessions.
* Configure and advertise same IPv4 routes from both the test ports.
* Configure another IPv4 session to send the traffic. This is the server port from which traffic will be sent to the VIP [Virtual IP] addresses.
* Start all protocols and verify that IPv4 BGP neighborship is established.
* Create a data traffic between the server port and receiver ports where the same VIP addresses are configured and enable tracking by "Destination Endpoint" and by "Destination session description".
* Set the desired threshold value for receiving traffic. By default it will be set to 95% of expected receiving rate.
* Apply and start the data traffic.
* Verify that traffic is equally distributed between the receiving ports without any loss.
* Simulate local link failure by making port down on test tool. 
* Verify that the traffic is re-balanced and use the other available path to route the traffic.
* Compute the failover convergence by the below formula
* Data Convergence Time(seconds) = (Tx Frames - Rx Frames) / Tx Frame Rate

### Test Results
Below table is the result of 3 way ECMP for 4 link flap iterations
| Event Name | No. of IPv4 Routes  | Iterations  | Avg Calculated Data Convergence Time(ms)  |
| :---:   | :-: | :-: | :-: |
| Test_Port_2 Link Failure | 1000 | 4 | 22.312 |
| Test_Port_3 Link Failure | 1000 | 4 | 16.0 |
| Test_Port_4 Link Failure | 1000 | 4 | 24.0 |
