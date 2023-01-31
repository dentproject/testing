# Description

This is the directory to document how to start/run the tests from the scratch.

## Hardware Requirements

* 7 Dentos Devices.
* 1 Ixia Chassis with 16 10G port running IxOS/IxNetwork EA versions [We are using 9.20 EA].
* 1 IxNetwork EA API server.
* 1 linux with Ubuntu 22.04 (centos8 will also work or other distributions but the instructions bellow are for ubuntu 22.04)
TODO: create a lab BOM

## Prepare Testbed Server

* Install Ubuntu[^1] 22.04 x64 on the server. ([ubuntu-22.04.1-live-server-amd64.iso](https://releases.ubuntu.com/22.04/))
  * select all default options (unless otherwise noted bellow)
  * on disk setup: disable LVM (optional)
  * on profile setup: put name, servername, username, password all as `dent` for example purposes
  * on ssh setup: enable `install OpenSSH server`
* Install Ubuntu prerequisites

```Shell
    sudo apt -y update
    sudo apt -y upgrade
    sudo apt -y autoremove
    sudo apt -y install \
      python3 \
      python3-pip \
      net-tools \
      curl \
      git \
      make
    sudo apt -y install ubuntu-desktop (TODO: remove this depedency)
```

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

* install KVM (required by IxNetwork API server)

```Shell
    sudo apt -y install cpu-checker
    sudo kvm-ok
    sudo apt -y install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager libosinfo-bin
    sudo usermod -aG libvirt $USER
    sudo usermod -aG kvm $USER
    sudo systemctl enable libvirtd
    sudo systemctl start libvirtd
```

* enable root (optional)

```Shell
    sudo sed -i "s/#PermitRootLogin prohibit-password/PermitRootLogin yes/g" /etc/ssh/sshd_config
    echo 'root:YOUR_PASSWORD' | sudo chpasswd
    sudo systemctl restart sshd
```

* setup management port configuration using this sample `/etc/netplan/00-installer-config.yaml`:

```code
  ---
  network:
    ethernets:
      ens160:
        dhcp4: false
        dhcp6: false
    bridges:
      br1:
        interfaces: [ens160]
        addresses: [10.36.118.210/24]
        routes:
    - to: default
      via: 10.36.118.1
        mtu: 1500
        nameservers:
          addresses: [4.4.4.4, 8.8.8.8]
        parameters:
    stp: false
    forward-delay: 0
    max-age: 0
        dhcp4: false
        dhcp6: false
    version: 2
```

* check the yaml file is ok (optional)

```Shell
sudo apt -y install yamllint
yamllint /etc/netplan/00-installer-config.yaml
```

* reboot
  * ensure networking is ok
  * this is needed also for the permissions to be update, otherwise next step will fail

* clone the `dentproject/testing` repository into your working directory:

```Shell
git clone https://github.com/dentproject/testing
```

* build container

```Shell
docker build --no-cache --tag dent/test-framework:latest ./testing/framework
docker tag dent/test-framework:latest dent/test-framework:1.0.0
```

* VMs
  * create vms folder

  ```Shell
  sudo mkdir /vms
  sudo chmod 775 -R /vms
  ```

  * download [IxNetwork kvm image](https://downloads.ixiacom.com/support/downloads_and_updates/public/ixnetwork/9.30/IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2).
  * copy `IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2` to `/vms/` on your testbed server.

* start the VMs:

```Shell
cd /vms

sudo tar xjf IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2

virt-install --name IxNetwork-930 --memory 16000 --vcpus 8 --disk /vms/IxNetworkWeb_KVM_9.30.2212.22.qcow2,bus=sata --import --os-variant centos7.0 --network bridge=br1,model=virtio --noautoconsole
virsh autostart IxNetwork-930

```

* configure the IxNetwork VM ip:

```Shell
    virsh console IxNetwork-930 --safe
```

  if a dhcp server is present we can obseve the IP assigned

```code
  dent@dent:~$ virsh console IxNetwork-930 --safe
  Connected to domain 'IxNetwork-930'
  Escape character is ^] (Ctrl + ])

  CentOS Linux 7 (Core)
  Kernel 3.10.0-693.21.1.el7.x86_64 on an x86_64

  Ixia
  System initializing, it may take few seconds to become available.

  The IPv4 address is 10.36.118.214 (MAC address 52:54:00:9e:4e:8f)
  Enter `https://10.36.118.214` in your web browser to access the application
  The IPv6 link-local address is fe80::5054:ff:fe9e:4e8f
  The IPv6 global address is not configured
  To change the IP address, log in as admin (password: admin) below
```

## To run the test cases below are the steps

  1. Create the Linux [we used CentOS8 VM] testbed where you will run/debug the cases.
  2. Create the DentOS cloud with DENT-Aggregator, DENT-Distributor & DENT-Infrastructure DUTs.
  3. Install DentOS on DUTs
  4. Run the tests.
  5. Check Logs locally at `./testing/Amazon_Framework/DentOsTestbed/logs`

we will go through the process/steps in details below -

### 1. Create the linux [we used centos8 vm] testbed

* a. [Installing all packages](https://github.com/dentproject/testing/DentOS_Framework/README.md)
* b. Copy all test files to the linux. copy/forge the directory `https://github.com/dentproject/testing/DentOS_Framework` to your local Linux
* c. change the testbed settings change the `testbed.json` as per your current testbed at `./testing/Amazon_Framework/DentOsTestbed/configuration/testbed_config/sit`

### 2. As per the testbed diagram we will connect all required cables among DUTs[DENT devices] and Keysight devices

[System integration test bed](https://github.com/dentproject/testing/docs/System_integration_test_bed)

### 3. install DentOS on the DUTs

To install DentOS follow the instructions here `TODO: add link here`

### 4. Run the tests

After you finish steps 1, 2 & 3 and make sure all boxes are up with proper IP address that you gave on the settings file.

Also make sure they are pinging each other.

Now go to directory /root/testing/Amazon_Framework/DentOsTestbed/ and run below commands

```Shell
dentos_testbed_runtests -d --stdout \
  --config configuration/testbed_config/sit/testbed.json \
  --config-dir configuration/testbed_config/sit/ \
  --suite-groups suite_group_clean_config \
  --discovery-reports-dir DISCOVERY_REPORTS_DIR \
  --discovery-reports-dir ./reports \
  –-discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/
```

This will check the connectivity and basically make the environment.

### How to Run all cases

```Shell
dentos_testbed_runtests -d --stdout \
  --config configuration/testbed_config/sit/testbed.json \
  --config-dir configuration/testbed_config/sit/ \
  --suite-groups suite_group_test suite_group_l3_tests suite_group_basic_trigger_tests suite_group_traffic_tests suite_group_tc_tests suite_group_bgp_tests \
                 suite_group_stress_tests suite_group_system_wide_testing suite_group_system_health suite_group_store_bringup suite_group_alpha_lab_testing \
                 suite_group_dentv2_testing suite_group_connection suite_group_platform \
  --discovery-reports-dir DISCOVERY_REPORTS_DIR \
  --discovery-reports-dir ./reports \
  --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/
```

### How to run a single test case

```Shell
dentos_testbed_runtests -d --stdout \
  --config configuration/testbed_config/sit/testbed.json \
  --config-dir configuration/testbed_config/sit/ \
  --suite-groups <suite group name> \
  --discovery-reports-dir DISCOVERY_REPORTS_DIR \
  --discovery-reports-dir ./reports \
  --discovery-path ../DentOsTestbedLib/src/dent_os_testbed/discovery/modules/ <testcase from the suit>
```

 [^1]: it can be also centos archlinux .... but the example commands shown are for ubuntu
