# Mandatory settings by users
export DENT_SERVER_IP_ADDRESS="10.36.118.11"
export DENT_IxNETWORK_VM_DHCP_MAC_ADDRESS="00:1a:c5:00:00:12"

# Edit below values only when you need to update IxNetwork
export DENT_IXNETWORK_VM_IMAGE="https://downloads.ixiacom.com/support/downloads_and_updates/public/ixnetwork/9.30/IxNetworkWeb_KVM_9.30.2212.22.qcow2.tar.bz2"

# Optional: User could set this setting
#           How many days do you want to keep test results?
export DENT_REMOVE_PAST_RESULTS_AFTER_DAYS=10

# Optional: Default URL for downloading latest DentOS builds
export DENT_DOWNLOAD_BUILD_URL="https://repos.refinery.dev/service/rest/repository/browse/dent/snapshots/org/dent/dentos/dentos-verify-main/"

# Should not touch below settings
export DENT_BASE_DIR="/home/dent"
export DENT_CI_FRAMEWORK_PATH="/home/dent/testing/CI_Automation"
export DENT_HTTP_SERVER_BUILDS_FOLDER="/DentBuildReleases"
