#### MANUAL CONFIG ####
N_LOAD_MODULES 	= 4

CTL_BRIDGE 	= br1
CTL_MAC		= ea:5f:f0:bc:96:aa

CLIENT_MAC 	= 00:1a:c5:00:00:13
# CLIENT_IP  	= 10.36.118.112

CHASSIS_MAC = 00:1a:c5:00:00:20
# CHASSIS_IP  = 10.36.118.150

LOAD_MAC 	= 00:1a:c5:00:00:31 00:1a:c5:00:00:32 	00:1a:c5:00:00:33 	00:1a:c5:00:00:34
# LOAD_IP 	= 10.36.118.161 	10.36.118.162 		10.36.118.163 		10.36.118.164
LOAD_PCI	= pci_0000_65_00_0	pci_0000_65_00_1	pci_0000_65_00_2	pci_0000_65_00_3

#### AUTO CONFIG #####
DEFAULT_NETDEV = $(shell ip route | grep 'default' | cut -d " " -f 5)
DEFAULT_IP	   = $(shell ip a show $(DEFAULT_NETDEV) | grep -w 'inet' | cut -d " " -f 6 )
DEFAULT_GATEWAY = $(shell ip route | grep 'default' | cut -d " " -f 3)

LOAD_MODULES 	= $(shell seq $(N_LOAD_MODULES))

BZ2S 	= $(wildcard *.bz2 download/*.bz2)
QCOWS 	= $(addprefix backups/, $(basename $(basename $(notdir $(BZ2S)))))

#### Colors ####
BLUE=\033[0;34m
NOCOLOR=\033[0m

#### Manual Targets ####
.PHONY: all help extract vm_overwrite download deploy

all help:
	@echo "Getting Started: Edit the MANUAL CONFIG section of the Makefile"
	@echo "Setup Targets: download and install VMs"
	@echo "\t$(BLUE)make download$(NOCOLOR)\t\t URL instructions to download bz2s"
	@echo "\t$(BLUE)make deploy$(NOCOLOR)\t\t Execute following installation steps in order"
	@echo "Installation Step Targets: (If Deploy Fails)"
	@echo "\t$(BLUE)make deps$(NOCOLOR)\t\t install all dependencies"
	@echo "\t$(BLUE)make bridge_configure$(NOCOLOR)\t automatically setup network bridge"
	@echo "\t$(BLUE)make extract$(NOCOLOR)\t\t extract qcow2 images from downloaded bz2s"
	@echo "\t$(BLUE)make vm_overwrite$(NOCOLOR)\t create or replace VM images with backups"
	@echo "\t$(BLUE)make vm_install$(NOCOLOR)\t\t Install all VMs"
	@echo "Utility Targets":
	@echo "\t$(BLUE)make vm_undefine$(NOCOLOR)\t remove installed vms so reinstall can occur"
	@echo "\t$(BLUE)make vm_reboot$(NOCOLOR)\t\t reboot all active VMs"
	@echo "\t$(BLUE)make vm_shutdown$(NOCOLOR)\t shutdown all active VMs"
	@echo "\t$(BLUE)make vm_start$(NOCOLOR)\t\t start all inactive VMs"
download:
	mkdir -p download
	@echo Download the following files to current directory or "download" folder, login may be required
	@echo https://downloads.ixiacom.com/support/downloads_and_updates/public/ixnetwork/9.30/IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2
	@echo https://downloads.ixiacom.com/support/downloads_and_updates/public/IxVM/9.30/9.30.0.328/Ixia_Virtual_Load_Module_IXN_9.30_KVM.qcow2.tar.bz2
	@echo https://downloads.ixiacom.com/support/downloads_and_updates/public/IxVM/9.30/9.30.0.328/Ixia_Virtual_Chassis_9.30_KVM.qcow2.tar.bz2

deploy: check_sure deps dirs bridge_configure extract chassis_reset load_reset client_reset vm_install

deps:
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

	sudo apt -y install cpu-checker
	sudo kvm-ok
	sudo apt -y install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager libosinfo-bin bzip2
	sudo usermod -aG libvirt $(USER)
	sudo usermod -aG kvm $(USER)
	sudo systemctl enable libvirtd
	sudo systemctl start libvirtd
	
# Create Directories and Extract if Necessary
extract: dirs $(QCOWS)

bridge_configure:  00-installer-config_generated.yaml
00-installer-config_generated.yaml:
	cp 00-installer-config.yaml 00-installer-config_generated.yaml
	sed -i 's/DEFAULT_NETDEV/$(DEFAULT_NETDEV)/g' 00-installer-config_generated.yaml 
	sed -i 's,DEFAULT_IP,$(DEFAULT_IP),g' 00-installer-config_generated.yaml 
	sed -i 's/DEFAULT_GATEWAY/$(DEFAULT_GATEWAY)/g' 00-installer-config_generated.yaml
	sed -i 's/CTL_MAC/$(CTL_MAC)/g' 00-installer-config_generated.yaml
	sudo mkdir -p /etc/netplan/old 
	sudo mv /etc/netplan/00-installer-config.yaml /etc/netplan/old
	sudo cp 00-installer-config_generated.yaml /etc/netplan/00-installer-config.yaml
	sudo netplan apply
	sudo ufw allow in on $(CTL_BRIDGE)
	sudo ufw route allow in on $(CTL_BRIDGE)
	sudo ufw route allow out on $(CTL_BRIDGE)	

# CAUTION: OVERWRITES EXISTING VMS
vm_overwrite: check_sure dirs chassis_reset load_reset client_reset

vm_install:
# Let Libvirt Read Files
	sudo setfacl -m u:libvirt-qemu:rx ~
# Install Client
	virt-install --name IxNetwork-930 --memory 8000 --vcpus 4 \
		--disk client/client.qcow2,bus=sata --import --os-variant centos7.0 \
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(CLIENT_MAC) --noautoconsole	
	virsh autostart IxNetwork-930

# Install Chassis
	virt-install --name IxChassis-930 --memory 8000 --vcpus 4 \
		--disk chassis/chassis.qcow2,bus=sata --import --os-variant centos7.0 	\
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(CHASSIS_MAC) --noautoconsole	
	virsh autostart IxChassis-930
# Install Load Modules
	$(foreach LMI, $(LOAD_MODULES),\
	virt-install --name IxLoad$(LMI)-930 --memory 4000 --vcpus 4 						\
		--disk load/load$(LMI).qcow2,bus=sata --import --osinfo detect=on,require=off 			\
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(word $(LMI), $(LOAD_MAC)) --noautoconsole	\
		--host-device=$(word $(LMI), $(LOAD_PCI)) ;											\
	virsh autostart IxLoad$(LMI)-930;	\
	)

vm_undefine:
	$(foreach vm, $(shell virsh list --name), 		virsh destroy $(vm);)
	$(foreach vm, $(shell virsh list --all --name), virsh undefine $(vm);)

vm_reboot:
	$(foreach vm, $(shell virsh list --name), 		virsh reboot $(vm);)

vm_shutdown:
	$(foreach vm, $(shell virsh list --name), 		virsh shutdown $(vm);)

vm_start:
	$(foreach vm, $(shell virsh list --all --name), virsh start  $(vm);)
### Helper Targets ####

check_sure:
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]

chassis_reset:
	cp $(shell find backups/ -iname '*chassis*') chassis/chassis.qcow2 -f

load_reset:
	$(foreach n, $(LOAD_MODULES), cp $(shell find backups/ -iname '*load*') load/load$(n).qcow2 -f;) 

client_reset:
	cp $(shell find backups/ -iname '*network*') client/client.qcow2 -f

backups/%.qcow2:
	if [ -f $*.qcow2.tar.bz2 ]; then mv $*.qcow2.tar.bz2 download/ ;fi;
	tar -xf download/$*.qcow2.tar.bz2 --use-compress-program=lbzip2 -C backups

#Create Directories
dirs: backups/ chassis/ client/ load/ download/

# Folder Creation
%/ : 
	mkdir $@

