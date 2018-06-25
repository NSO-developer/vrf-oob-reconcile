#!/bin/sh

set -e

if [ ! -d netsim ]; then

    ncs-netsim --dir netsim  \
               create-device device-nodes/packages/cisco-iosxr xr0\
               create-device device-nodes/packages/cisco-iosxr xr1\
               create-device device-nodes/packages/cisco-iosxr xr2\
               create-device device-nodes/packages/cisco-iosxr xr3\

fi

for i in `echo 1 2`; do
    dir=device-nodes/nso-${i}/
    mkdir ${dir}/ncs-cdb;
    mkdir ${dir}/logs
    mkdir ${dir}/state
done

dir=service-node
mkdir ${dir}/ncs-cdb;
mkdir ${dir}/logs
mkdir ${dir}/state

for i in `echo 1 2`; do
    echo '<config xmlns="http://tail-f.com/ns/config/1.0">' > \
         device-nodes/nso-${i}/ncs-cdb/netsim_devices_init.xml
done

ncs-netsim ncs-xml-init xr0 >> device-nodes/nso-1/ncs-cdb/netsim_devices_init.xml
ncs-netsim ncs-xml-init xr2 >> device-nodes/nso-1/ncs-cdb/netsim_devices_init.xml
ncs-netsim ncs-xml-init xr1 >> device-nodes/nso-2/ncs-cdb/netsim_devices_init.xml
ncs-netsim ncs-xml-init xr3 >> device-nodes/nso-2/ncs-cdb/netsim_devices_init.xml

for i in `echo 1 2`; do
     echo '</config>' >> \
         device-nodes/nso-${i}/ncs-cdb/netsim_devices_init.xml
done
