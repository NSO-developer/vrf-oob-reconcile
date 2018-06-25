#!/bin/sh

set -e

ncs_cli -u admin <<EOF
configure
load merge init-data/nsos.xml
commit
load merge init-data/cluster.xml
commit
load merge init-data/dispatch.xml
commit
request cluster remote-node nso-1 ssh fetch-host-keys
request cluster remote-node nso-2 ssh fetch-host-keys
commit
request devices fetch-ssh-host-keys
request devices sync-from
commit
exit
exit
EOF
