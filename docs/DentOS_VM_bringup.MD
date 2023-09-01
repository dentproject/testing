# Bringing Up dentOS VM

This document details the post-installation steps to bring up a fresh dentOS VM.

* To deploy the dentOS VM, see [VM testbed bringup](How_to_bringup_VM_testbed.md)
* To install a fresh version of dentOS on the VM:
  * connect to the VM with `virsh console <dent-vm-name>`
  * reboot the VM and boot into `ONIE` mode
  * Run `onie-nos-install <link.to.installation.image>`

## Update Date/Time via NTP Servers

Check that a newly install dentOS VM has the right date by verifying the output of the `date` command. If it is wrong, `NTP` servers may need to be updated using the command below.

```Shell
ntpdate time.nist.gov
```

## Update Packages

```Shell
apt update -y
apt install curl apt-transport-https bridge-utils
```

## Change Port Naming using `/etc/rc.local`

DentOS and its testbed expects switch ports to be named with the convention `swpN`, but software bridge ports are named differently. The correct naming can be achieved by editing `rc.local` so that the ports are renamed on startup:

```Shell
echo '#!/bin/sh -e
sleep 5
ip link set enp0s4 name swp1
ip link set enp0s5 name swp2
ip link set enp0s6 name swp3
ip link set enp0s7 name swp4' > /etc/rc.local
chmod +x /etc/rc.local
```

## FRRouting Install

`FRRouting` is a key service for network protocols. Check its status using:

```systemctl status frr.service```

 If it is not found by default, it should be installed below. See https://deb.frrouting.org/ for full instructions.

```Shell
# add GPG key
curl -s https://deb.frrouting.org/frr/keys.gpg | sudo tee /usr/share/keyrings/frrouting.gpg > /dev/null

# possible values for FRRVER: frr-6 frr-7 frr-8 frr-9 frr-stable
# frr-stable will be the latest official stable release
FRRVER="frr-stable"
echo deb '[signed-by=/usr/share/keyrings/frrouting.gpg]' https://deb.frrouting.org/frr \
     $(lsb_release -s -c) $FRRVER | sudo tee -a /etc/apt/sources.list.d/frr.list

# update and install FRR
sudo apt update && sudo apt install frr frr-pythontools
```

## Update Petunia from Source

[Petunia](https://github.com/dentproject/petunia) is a necessary tool that works with `tc-flower`. Check the date on the binary using:

```ls -l /usr/bin/tc-flower-load```

Update if necessary following the steps below.

```Shell
apt update -o
apt install git debhelper -y
git clone https://github.com/dentproject/dentOS.git
cd dentOS
sudo ./docker/tools/onlbuilder
cd sm
git clone https://github.com/dentproject/petunia.git
cd petunia
apt update
apt install python3-pip python3-all -y
pip3 install stdeb
python3 setup.py --command-packages=stdeb.command bdist_deb
dpkg -i deb_dist/python3-petunia_1.0-1_all.deb
```
