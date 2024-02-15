#### INSTALLATION TARGETS ####
SOFT_TESTBED = dvm_install # Comment out this line if you don't want the dent-vm software testbed
HARD_TESTBED = vlm_install # Comment out this line if you don't want the hardware-connected vm testbed

#### MANUAL CONFIG - IxNetwork/IxChassis VMS ####
CTL_BRIDGE 	= br1
CTL_MAC		= ea:5f:f0:bc:96:aa

CLIENT_MAC 	= 00:1a:c5:00:00:13

CHASSIS_MAC = 00:1a:c5:00:00:20

#### MANUAL CONFIG - HW DUT VLMs ####
# Ensure LOAD_MAC and LOAD_PCI have N_LOAD_MODULES items each
N_LOAD_MODULES 	= 4
LOAD_MAC 	= 00:1a:c5:00:00:31 00:1a:c5:00:00:32 	00:1a:c5:00:00:33 	00:1a:c5:00:00:34
LOAD_PCI	= pci_0000_65_00_0	pci_0000_65_00_1	pci_0000_65_00_2	pci_0000_65_00_3

#### MANUAL CONFIG - DENTVM DUT + VLM ####
N_CONNECTS 	 = 4	# If changed, update the interfaces in 'dent/dent-vm.xml'
DVM_LOAD_MAC = 00:1a:c5:00:00:35

#### AUTO CONFIG #####
QEMU_DIR = /etc/libvirt/qemu

DEFAULT_NETDEV = $(shell ip route | grep 'default' | cut -d " " -f 5)
DEFAULT_IP	   = $(shell ip a show $(DEFAULT_NETDEV) | grep -w 'inet' | cut -d " " -f 6 )
DEFAULT_GATEWAY = $(shell ip route | grep 'default' | cut -d " " -f 3)

LOAD_MODULES 	= $(shell seq $(N_LOAD_MODULES))

BZ2S 	= $(wildcard *.bz2 download/*.bz2)
QCOWS 	= $(addprefix backups/, $(basename $(basename $(notdir $(BZ2S)))))

TARGETS  = mgm_install
TARGETS += $(SOFT_TESTBED)
TARGETS += $(HARD_TESTBED)

RESET = client_reset chassis_reset
ifdef $(HARD_TESTBED)
RESET += load_reset
endif
ifdef $(SOFT_TESTBED)
RESET += loadVM_reset
RESET += dent_reset
endif

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
	@echo https://repos.refinery.dev/repository/dent/public/org/test/vm/dent-vm.tar.bz2

deploy: check_sure deps dirs bridge_configure extract $(RESET) vm_install

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
# Let Libvirt Read Files
	sudo setfacl -m u:libvirt-qemu:rx .

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

dvm_bridges: $(foreach N, $(shell seq $(N_CONNECTS)), $(QEMU_DIR)/networks/dent_virbr$(N).xml)
$(QEMU_DIR)/networks/dent_virbr%.xml:
	cp dent/dent_vbridgeN.xml dent/dent_vbridge$*.xml
	sed -i 's/NUM/$*/g' dent/dent_vbridge$*.xml
	virsh net-define dent/dent_vbridge$*.xml
	virsh net-autostart dent_virbr$*
	virsh net-start dent_virbr$*
	rm dent/dent_vbridge$*.xml

# CAUTION: OVERWRITES EXISTING VMS
vm_overwrite: check_sure dirs $(RESET)

# Install Configured Targets: mgm_install, dvm_install, vlm_install
vm_install: $(TARGETS)

# Install Management VMS: IxNetwork, IxChassis
mgm_install:  $(QEMU_DIR)/IxNetwork-930.xml $(QEMU_DIR)/IxChassis-930.xml

# Install Client
$(QEMU_DIR)/IxNetwork-930.xml:
	virt-install --name IxNetwork-930 --memory 8000 --vcpus 6 \
		--disk client/client.qcow2,bus=sata --import --os-variant centos7.0 \
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(CLIENT_MAC) --noautoconsole
	virsh autostart IxNetwork-930

# Install Chassis
$(QEMU_DIR)/IxChassis-930.xml:
	virt-install --name IxChassis-930 --memory 8000 --vcpus 4 \
		--disk chassis/chassis.qcow2,bus=sata --import --os-variant centos7.0 	\
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(CHASSIS_MAC) --noautoconsole
	virsh autostart IxChassis-930

#Install Dent VM DUT and connected VLM
dvm_install: dvm_bridges $(QEMU_DIR)/dent-vm.xml $(QEMU_DIR)/IxLoadVM-930.xml

$(QEMU_DIR)/dent-vm.xml:
	sed -i "s,file='.*qcow2',file='$(shell pwd)/dent/dent.qcow2',g" dent/dent-vm.xml
	virsh define dent/dent-vm.xml
	virsh start dent-vm
	virsh autostart dent-vm

$(QEMU_DIR)/IxLoadVM-930.xml:
	virt-install --name IxLoadVM-930 --memory 4000 --vcpus 10							\
		--disk load/loadVM.qcow2,bus=sata --import --osinfo detect=on,require=off 		\
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(DVM_LOAD_MAC) --noautoconsole \
		$(foreach N, $(shell seq $(N_CONNECTS)),--network network=dent_virbr$(N)) 		\
	virsh autostart IxLoadVM-930

# Install Virtual Load Modules w/ PCI Passthrough
vlm_install: $(foreach LMI, $(LOAD_MODULES), $(QEMU_DIR)/IxLoad$(LMI)-930.xml )

# Install Load Modules
$(QEMU_DIR)/IxLoad%-930.xml:
	virt-install --name IxLoad$*-930 --memory 4000 --vcpus 4 						\
		--disk load/load$*.qcow2,bus=sata --import --osinfo detect=on,require=off 			\
		--network bridge=$(CTL_BRIDGE),model=virtio,mac=$(word $*, $(LOAD_MAC)) --noautoconsole	\
		--host-device=$(word $*, $(LOAD_PCI)) ;											\
	virsh autostart IxLoad$*-930	\

#### Utility Targets ####

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

load_reset: $(foreach n, $(LOAD_MODULES), load$(n)_reset)
load%_reset:
	cp $(shell find backups/ -iname '*load*') load/load$*.qcow2 -f

client_reset:
	cp $(shell find backups/ -iname '*network*') client/client.qcow2 -f

%_reset:
	cp $(shell find backups/ -iname '*$**') $*/$*.qcow2 -f

backups/%:
	if [ -f $*.tar.bz2 ]; then mv $*.tar.bz2 download/ ;fi;
	tar -xf download/$*.tar.bz2 --use-compress-program=lbzip2 -C backups

#Create Directories
dirs: backups/ chassis/ client/ load/ download/

# Folder Creation
%/ :
	mkdir $@
