# Description

This file documents the hardware testbed setup using IxNetwork VM on an Ubuntu 22.04 Server with an Ixia Hardware Chassis.

## Table of content

1. [Hardware Requirements](#hardware-requirements)
1. [Prepare Testbed Server](#prepare-testbed-server)
1. [Set Up Network](#setup-network)
1. [Install IxNetwork VE](#install-ixnetwork-ve)
1. [License IxNetwork VE](#license-ixnetwork-ve)
## Hardware Requirements

* 4-7 DentOS Devices.
* 1 Ixia Chassis with 16 10G port running IxOS/IxNetwork EA versions [We are using 9.20 EA].
* 1 IxNetwork EA API server.
* 1 linux with Ubuntu 22.04 Server (centos8 will also work or other distributions but the instructions bellow are for ubuntu 22.04)
TODO: create a lab BOM

## Prepare Testbed Server

### Install OS

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
      make \
      lbzip2
    sudo apt -y install ubuntu-desktop (TODO: remove this dependency)
```

* enable root ssh access (optional)

```Shell
    sudo sed -i "s/#PermitRootLogin prohibit-password/PermitRootLogin yes/g" /etc/ssh/sshd_config
    echo 'root:YOUR_PASSWORD' | sudo chpasswd
    sudo systemctl restart sshd
```

### Install KVM

* install KVM (required by IxNetwork API server)

```Shell
    sudo apt -y install cpu-checker
    sudo kvm-ok
    sudo apt -y install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager libosinfo-bin bzip2
    sudo usermod -aG libvirt $USER
    sudo usermod -aG kvm $USER
    sudo systemctl enable libvirtd
    sudo systemctl start libvirtd
```

## Setup Network
A VM must be able to access the network through a bridge connected to the server's main ethernet adapter. This is done in Ubuntu using netplan:
* setup management port configuration using this sample by editing `/etc/netplan/00-installer-config.yaml`:

```Yaml
---
network:
  ethernets:
    eth_used: # Connected Ethernet Device (maybe eth0)
      dhcp4: false
      dhcp6: false
    eth_unused: # Unused Ethernets
      dhcp4: false
      dhcp6: false
      optional: true  # Set optional for faster boot time
  bridges:
    br1:
      interfaces: [eth_used] # Bridge connected to ethernet
      addresses: [10.36.118.11/24] # Server IP
      routes:
        - to: default
          via: 10.36.118.1  # Default Gateway
      mtu: 1500
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8, 156.140.198.11, 156.140.214.11]
      parameters:
        stp: false
        forward-delay: 0
        max-age: 0
      dhcp4: false
      dhcp6: false
  version: 2
  # Network Renderer Choice: Network Manager can be installed for GUI support, but unncessary
  renderer: networkd
  # renderer: NetworkManager 
```

* check the yaml file is ok (optional)

```Shell
sudo apt -y install yamllint
yamllint /etc/netplan/00-installer-config.yaml
```
* Apply Netplan and Edit Firewall Settings to allow IxNetwork DHCP Resolution on bridge:
  * ```Shell
    sudo netplan apply
    sudo ufw allow in on br1
    sudo ufw route allow in on br1
    sudo ufw route allow out on br1
    ```
* reboot
  * ensure networking is working, for example verify output received from ```curl www.google.com```
  * this is needed also for the permissions to be update, otherwise next step will fail

## Install IxNetwork VE

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

sudo tar xjf IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2 --use-compress-program=lbzip2

virt-install --name IxNetwork-930 --memory 16000 --vcpus 8 --disk /vms/IxNetworkWeb_KVM_9.30.2212.22.qcow2,bus=sata --import --os-variant centos7.0 --network bridge=br1,model=virtio --noautoconsole
virsh autostart IxNetwork-930

```
  * Optionally use the following network flag to specify a mac address for use with a DHCP server:
    * ``` --network bridge=br1,model=virtio,mac=01:23:45:67:89:AB``` 
* configure the IxNetwork VM ip:

```Shell
    virsh console IxNetwork-930 --safe
```

  if a dhcp server is present we can observe the IP assigned

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
## License IxNetwork VE
Before tests can be run, IxNetwork VE must be licensed. From the start page, Settings Gear -> Administration -> License Manager provides an easy way to locally host a license. Once licensed, see the doc on [running testcases](How_to_start_and_run_testcases.md).
