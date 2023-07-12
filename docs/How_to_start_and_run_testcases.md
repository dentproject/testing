# Description

This is the directory to document how to run test cases once your HW or VM testbed is set up.

## Table of Contents

1. [Getting Started](#getting-started)
1. [Running DentOS SIT tests](#running-dentos-sit-tests)
1. [Running DentOS Functional tests](#running-dentos-functional-tests)

## Getting Started
### Install docker

* install Docker (all credits to [Docker manual](https://docs.docker.com/engine/install/ubuntu/) )

```Shell
    sudo apt-get -y remove docker docker-engine docker.io containerd runc
    sudo apt-get update
    sudo apt-get -y install \
      apt-transport-https \
      ca-certificates \
      curl \
      gnupg-agent \
      gnupg \
      lsb-release \
      software-properties-common
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo docker run hello-world
```

* add your user to docker group

```Shell
    sudo usermod -aG docker $USER
```

### Prepare test running environment
* clone the `dentproject/testing` repository into your working directory:

```Shell
git clone https://github.com/dentproject/testing

# optional change to a different branch
# cd ./testing
# git checkout <branch name>
```

* build container (optional)

To save the time during the actual test run and to validate the environment it's recommended to build a container now.

```Shell
cd DentOS_Framework
./run.sh dentos_testbed_runtests -h
```

You should see the help message from the DentOS framework.

## Running DentOS SIT tests

Overall steps:

  1. Setup Testbed Server
  2. Setup the DentOS [SIT topology](./System_integration_test_bed/README.md) with DENT-Aggregator, DENT-Distributor & DENT-Infrastructure DUTs
  3. Install DentOS on DUTs
  4. Run the tests
  5. Check Logs locally at `./DentOS_Framework/DentOsTestbed/logs`

We will go through the process/steps in details below -

### System Integration Testbed preparation

As per the testbed diagram connect all required cables among DUTs (DENT devices) and Keysight devices.

[System Integration Testbed](https://github.com/dentproject/testing/docs/System_integration_test_bed)

Change the testbed settings in the `testbed.json` as per your current testbed at `./DentOS_Framework/DentOsTestbed/configuration/testbed_config/sit`

### Install DentOS on the DUTs in SIT

To install DentOS follow the instructions here `TODO: add link here`

### Run the tests

Make sure all boxes are up with proper IP address that you gave on the settings file.
Also make sure they are pinging each other.

Go to directory `DentOS_Framework/` and run below commands:

```Shell
./run.sh dentos_testbed_runtests -d --stdout \
  --config configuration/testbed_config/sit/testbed.json \
  --config-dir configuration/testbed_config/sit/ \
  --suite-groups suite_group_clean_config \
  --discovery-reports-dir ./reports \
  –-discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/
```

This will check the connectivity and basically make the environment.

### Run all SIT test cases

```Shell
./run.sh dentos_testbed_runtests -d --stdout \
  --config configuration/testbed_config/sit/testbed.json \
  --config-dir configuration/testbed_config/sit/ \
  --suite-groups suite_group_test suite_group_l3_tests suite_group_basic_trigger_tests suite_group_traffic_tests suite_group_tc_tests suite_group_bgp_tests \
                 suite_group_stress_tests suite_group_system_wide_testing suite_group_system_health suite_group_store_bringup suite_group_alpha_lab_testing \
                 suite_group_dentv2_testing suite_group_connection suite_group_platform \
  --discovery-reports-dir ./reports \
  --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/
```

### Run a single test case

```Shell
./run.sh dentos_testbed_runtests -d --stdout \
  --config configuration/testbed_config/sit/testbed.json \
  --config-dir configuration/testbed_config/sit/ \
  --suite-groups <suite group name> \
  --discovery-reports-dir ./reports \
  --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ <test case from the suit>
```

## Running DentOS Functional tests

Overall steps:

  1. Setup Testbed Server (previous step)
  2. Setup the DentOS **Functional topology**
  3. Install DentOS on DUT or cleanup configuration if it was used by SIT before
  4. Run the tests
  5. Check Logs locally at `./DentOS_Framework/DentOsTestbed/logs`

### Functional Testbed preparation

Functional testbed consists of a single DentOS device connected to the IxNetwork using 4 links.
If you have already assembled SIT testbed according to the diagram, you can use any device out of it separately.

Change the testbed settings in the `testbed.json` as per your current testbed at `./DentOS_Framework/DentOsTestbed/configuration/testbed_config/basic_*` (NOTE: `basic_` prefix in subfolder names)

### Install DentOS on the DUT

To install DentOS follow the instructions here `TODO: add link here`

### Cleanup DUT configuration

After the running SIT regression DUTs are usually contains specific persistent network configuration which interferes with the functional test cases.

In the following example INFRA2 functional topology is used. Note the path to the configuration - `configuration/testbed_config/basic_infra2`.

Run the following commands to cleanup the device:

```Shell
./run.sh dentos_testbed_runtests --stdout \
  --config configuration/testbed_config/basic_infra2/testbed.json \
  --config-dir configuration/testbed_config/basic_infra2/ \
  --discovery-reports-dir /tmp \
  --suite-groups suite_group_clean_config
```

The test should pass and DUT should not contain any network configuration except the management port IP address.

### Run functional regression

```Shell
./run.sh dentos_testbed_runtests --stdout \
  --config configuration/testbed_config/basic_infra2/testbed.json \
  --config-dir configuration/testbed_config/basic_infra2/ \
  --discovery-reports-dir /tmp \
  --suite-groups suite_group_functional
```

### Run specific functional tests/suites

Use `-k` option to select any specific test function or test suite from the selected test group.

Here are an example of how to run the VLAN test suite:

```Shell
./run.sh dentos_testbed_runtests --stdout \
  --config configuration/testbed_config/basic_infra2/testbed.json \
  --config-dir configuration/testbed_config/basic_infra2/ \
  --discovery-reports-dir /tmp \
  --suite-groups suite_group_functional \
  -k suite_functional_vlan
```

**NOTE:**

1. To avoid re-installing of the DentOS framework on each run command just enter the docker container and run multiple commands from inside.
2. You can use all supported pytest CLI arguments. dentos_testbed_runtests passes all unrecognized by arguments directly to the pytest.

```Shell
./run.sh
dentos_testbed_runtests -h
dentos_testbed_runtests --stdout \
  --config configuration/testbed_config/basic_infra2/testbed.json \
  --config-dir configuration/testbed_config/basic_infra2/ \
  --discovery-reports-dir /tmp \
  --suite-groups suite_group_functional \
  -k suite_functional_vlan \
  --collectonly --pdb
```

---

 [^1]: it can be also CentOS Archlinux .... but the example commands shown are for Ubuntu.
