# For DentOS 

# Description
This is the directory to document how to install dentOS in a device.

Got DENTos image, say

"DENTOS-main_ONL-..._ARM64_INSTALLED_INSTALLER"

Rename it as “onie-installer”, Then you can install 'using an USB' or 'just by copying it' to the device.

Using USB -
##############################

Put it onto USB disk. Make sure the USB is formatted to FAT32 before putting the installer file.


Plug the USB disk into the device

In the device console, enter command 'onie-shell'

then type command run onie_bootcmd

After entering ONIE installing mode, ONIE should be able to discover the “onie-installer” on the USB disk and install it.

Just By Copying it locally -
###############################

mv DENTOS-main_ONL-..._ARM64_INSTALLED_INSTALLER onie-installer
 
cp onie-installer /onie-installer
 
onie-select install
 
reboot


you can also create a http server in the linux testbed and copy the build to the server.
#######################################################################################

lets say your http server's  DocumentRoot is /temp

then type command 'onie-shell'.

when # prompt appears then just type 

ONIE-NOS-INSTALL http://<Linux IP>/temp/DENTOS-main_ONL-..._ARM64_INSTALLED_INSTALLER

