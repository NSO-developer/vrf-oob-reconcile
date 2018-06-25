# vrf-oob-reconcile

An example of reconciling out-of-band NSO service configuration changes

# Purpose

The purpose of this example is provide an example of handling device configuration
changes with modify NSO service intent. The reconcile operation is accomplished using 
NSO configuration/service templates.

# Documentation

Appart from this file, the main documentation is the python code and associated
YANG file(s).

# Dependencies

In order to utilize all the functionality, you will need to have (in the path)
the following components.

* NSO 4.6.1+
* Python 2.7+ or 3+
* Cisco IOS-XR NED

# Build instructions

   Download and uncompress a copy of the cisco-iosxr NED and place in the
   device-node/packages directory

   make -C packages/tailf-ntool/src clean all

# Running the demonstration

