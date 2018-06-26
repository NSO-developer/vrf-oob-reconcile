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

## Execute the reconcile demonstration
  First start up the 3 node simulation and the 4 netsim devices

  make start

### Step(1) Log into the service node and create the VRF service
<pre>
   ncs_cli -u admin  

   admin@srv-nso> config  
   Entering configuration mode private  
   [ok][2018-06-26 10:55:56]  
  
   [edit]  
   admin@srv-nso% load merge VRF.xml  
   [ok][2018-06-26 10:52:30]  
  
   [edit]  
   admin@srv-nso% show services vrf   
   vrf TEST-1 {  
      description "NSO created VRF";  
      devices xr0 {  
          route-distinguisher 6500:100;  
          import-route-target 6500:101;  
          import-route-target 6500:102;  
          import-route-target 6500:103;  
          import-route-policy TEST-1-IMPORT;  
          export-route-policy TEST-1-EXPORT;
      }
      devices xr1 {
          route-distinguisher 6500:200;
          import-route-target 6500:201;
          import-route-target 6500:202;
          import-route-target 6500:203;
          import-route-policy TEST-1-IMPORT;
          export-route-policy TEST-1-EXPORT;
      }
   }
   [ok][2018-06-26 10:52:34]

   [edit]
   admin@srv-nso% commit
   Commit complete.
   [ok][2018-06-26 10:52:52]

   [edit]
   admin@srv-nso%
</pre>
### Step(2) Log into nso-1 and modify the service configuration
<pre>
  % ncs_cli -u admin -P 4692

  admin connected from 127.0.0.1 using console on DANISULL-M-73NJ
  admin@nso-1> 
  admin@nso-1> configure 
  Entering configuration mode private
  [ok][2018-06-26 11:13:44]

  [edit]
  admin@nso-1% load merge MAX.xml
  [ok][2018-06-26 11:13:55]

  [edit]
  admin@nso-1% load merge ROUTE-TARGET.xml 
  [ok][2018-06-26 11:14:02]

  [edit]
  admin@nso-1% show | compare
    devices {
       device xr0 {
           config {
               cisco-ios-xr:vrf {
                   vrf-list TEST-1 {
                       address-family {
                           ipv4 {
                               unicast {
                                   import {
                                       route-target {
  +                                        address-list 6500:300 {
  +                                        }
                                       }
                                   }
                                   maximum {
                                       prefix {
  +                                        limit 1000;
  +                                        mid-thresh 50;
                                       }
                                   }
                               }
                           }
                       }
                   }
               }
           }
       }
   }
  [ok][2018-06-26 11:14:08]

  [edit]
  admin@nso-1% commit
  Commit complete.
  [ok][2018-06-26 11:16:48]

  [edit]
  admin@nso-1%
</pre>

### Step(3) Verify the service is now out of sync
<pre>
  admin@srv-nso> request services vrf TEST-1 check-sync 
  Error: Network Element Driver: device nso-1: out of sync
  [error][2018-06-26 11:35:27]
  admin@srv-nso> *** ALARM out-of-sync: Device nso-1 is out of sync
  admin@srv-nso> request devices sync-from             
    sync-result {
      device nso-1
      result true
    }
    sync-result {
      device nso-2
      result true
    }
  [ok][2018-06-26 11:35:36]
  admin@srv-nso> request services vrf TEST-1 check-sync 
  in-sync false
  [ok][2018-06-26 11:35:41]
  admin@srv-nso> request services vrf TEST-1 re-deploy dry-run 
  cli {
      lsa-node {
          name nso-1
          data  devices {
                     device xr0 {
                         config {
                             cisco-ios-xr:vrf {
                                 vrf-list TEST-1 {
                                     address-family {
                                         ipv4 {
                                             unicast {
                                                 import {
                                                     route-target {
                -                                        address-list 6500:300 {
                -                                        }
                                                     }
                                                 }
                                                 maximum {
                                                     prefix {
                -                                        limit 1000;
                -                                        mid-thresh 50;
                                                     }
                                                 }
                                             }
                                         }
                                     }
                               }
                             }
                         }
                     }
                 }
               
    }
  }
</pre>
### Step(4) Execute the out-of-band reconcile command
<pre>
  [ok][2018-06-26 11:35:53]
  admin@srv-nso> 
  admin@srv-nso> request services vrf TEST-1 oob-reconcile 
  status success
  [ok][2018-06-26 11:39:25]
  admin@srv-nso> 
  System message at 2018-06-26 11:39:25...
  Commit performed by admin via tcp using OOB-REC-TEST-1.
  admin@srv-nso>
</pre>
### Step(5) Display the updated service configuration
<pre>
  Display the service configuration and verify the newly
  reconciled values are now part of the service configuration

  admin@srv-nso> show configuration services vrf TEST-1 
  description "NSO created VRF";
  devices xr0 {
      route-distinguisher  6500:100;
      import-route-target 6500:101;
      import-route-target 6500:102;
      import-route-target 6500:103;
      import-route-target 6500:300;  <==== Added
      import-route-policy  TEST-1-IMPORT;
      export-route-policy  TEST-1-EXPORT;
      max-prefix-limit     1000; <=== Added
      max-prefix-threshold 50;   <=== Added
  }
  devices xr1 {
      route-distinguisher 6500:200;
      import-route-target 6500:201;
      import-route-target 6500:202;
      import-route-target 6500:203;
      import-route-policy TEST-1-IMPORT;
      export-route-policy TEST-1-EXPORT;
  }
  [ok][2018-06-26 11:39:56]
  admin@srv-nso> 


  The reconcile operation is complete. You can also cause the reconcile
  operation to fail by set the description field in the VRF which isn't
  automatically reconciled. (load merge DESC.xml on the device node 
  and repeat the above steps)
</pre>
