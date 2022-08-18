# Description
This is the directory to document how to start/run the tests from the scratch.

Hardware Requirements :

################################

7 Dentos Devices.

1 Ixia Chassis with 16 10G port running IxOS/IxNetwork EA versions [We are using 9.20 EA].

1 IxNetwork EA API server.

1 linux with CentOS8 or higher. 

###################################


To run thease cases below are the steps :

  1. Create the Linux [we used CentOS8 VM] testbed where you will run/debug the cases.
  2. Create the DENTos cloud with DENT-Aggregator, DENT-Distributor & DENT-Infrastructure DUTs.
  3. Install dentOS on DUTs
  4. Run the tests.
  5. Check Logs locally at <Linux>/root/testing/Amazon_Framework/DentOsTestbed/logs
  

we will go through the process/steps in details below -

1. create the linux [we used centos8 vm] testbed >>
-------------------------------------------------------------------
       a. Installing all packages https://github.com/dentproject/testing/DentOS_Framework/README.md
 
       b. Copy all testfiles to the linux.
        copy/forge the directory https://github.com/dentproject/testing/DentOS_Framework to your local Linux 
 
       c. change the testbed settings
        change the testbed.json as per your current testbed at <Linux>/root/testing/Amazon_Framework/DentOsTestbed/configuration/testbed_config/sit
		
		
2.As per the testbed diagram we will connect all required cables among DUTs[DENT devies] and Ixia devices >>
-----------------------------------------------------------------------------------------------------------------

     https://github.com/dentproject/testing/docs/System_integration_test_bed


3. install dentOS on the DUTs >>
------------------------------------------

     To install dentOS follow the instructions here >> Link.
	 
4.Run the tests >>
---------------------------------------------------

 after you finish steps 1,2 & 3 and make sure all boxes are up with proper IP address that you gave on the settings file.
 
 and also make sure they are pinging each other.
 
 Now goto directory /root/testing/Amazon_Framework/DentOsTestbed/ and run below commands

 dentos_testbed_runtests -d --stdout --config configuration/testbed_config/sit/testbed.json --config-dir configuration/testbed_config/sit/ --suite-groups suite_group_clean_config --discovery-reports-dir DISCOVERY_REPORTS_DIR --discovery-reports-dir ./reports –discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/

 This will check the connectivity and basically make the environment.

 
>> How to Run all cases?

  dentos_testbed_runtests -d --stdout --config configuration/testbed_config/sit/testbed.json --config-dir configuration/testbed_config/sit/ --suite-groups suite_group_test suite_group_l3_tests suite_group_basic_trigger_tests suite_group_traffic_tests suite_group_tc_tests suite_group_bgp_tests suite_group_stress_tests suite_group_system_wide_testing suite_group_system_health suite_group_store_bringup suite_group_alpha_lab_testing suite_group_dentv2_testing suite_group_connection suite_group_platform --discovery-reports-dir DISCOVERY_REPORTS_DIR --discovery-reports-dir ./reports --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ 
 

>> How to run a single testcase?

  dentos_testbed_runtests -d --stdout --config configuration/testbed_config/sit/testbed.json --config-dir configuration/testbed_config/sit/ --suite-groups <suite group name> --discovery-reports-dir DISCOVERY_REPORTS_DIR --discovery-reports-dir ./reports --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ <testcase from the suit>
  
  
 
