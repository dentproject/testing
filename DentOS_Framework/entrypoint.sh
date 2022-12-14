#!/bin/bash

DENT_PACKAGES=("/DENT/DentOsTestbed" "/DENT/DentOsTestbedDiscovery" "/DENT/DentOsTestbedLib")
for pkg in ${DENT_PACKAGES[@]}; do
    cd $pkg
    # pip3 install --editable .  # Does not work for these packages
    pip3 install .
done

cd /DENT/DentOsTestbed

$@
