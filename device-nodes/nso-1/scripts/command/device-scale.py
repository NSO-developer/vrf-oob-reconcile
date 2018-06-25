#!/usr/bin/python
# Copyright 2014 Tail-f Systems
#

#
# Name: level3-migrate.py
#
# Author: Dan Sullivan
# Created: 01-Jun-2017
#
#

import _ncs
import _ncs.deprecated.maapi as maapi
import sys
import argparse
import re
import os
import subprocess
import socket

step = 1
services = []
port = 0
devcfg = ""

NO_NETWORKING = ( 1 << 4)

def print_ncs_command_details():
    print """
        begin command
            modes: config
            styles: c i j
            cmdpath: dev-replicate
            help: Command to clone devices
        end

        begin param
          name: from-device
          presence: mandatory
          flag: -f
          help: Device to migrate from
        end

        begin param
          name: name
          presence: mandatory
          flag: -n
          help: Device name prefix to start 
        end

        begin param
          name: dcount
          presence: mandatory
          flag: -d
          help: Number of devices to replicate
        end

        """

def copyDevice(th, sock, src, dst):
    global devcfg

    try:
         # Modify service XML to use new device
         pnew = re.sub('<name>' + src + '</name>', '<name>' + dst + '</name>', devcfg)
         
         # Load merge the updated service with the new device
         _ncs.maapi.load_config_cmds(sock, 
                                     th, 
                                     _ncs.maapi.CONFIG_MERGE | _ncs.maapi.CONFIG_XML,
                                     pnew, '')
         return True
    except Exception as e:
         
         print e.__class__
         return False

def devExists(t, devName):
    path = '/ncs:devices/device{"' + devName + '"}'
  
    if (t.exists(path)):
      return True

    return False 

def runCliCommand(command):
     #try:
       cmd=['ncs-maapi','--clicmd','--get-io', command]
       p1 = subprocess.check_output(cmd, shell=False)
       return p1
     #except:
       #return None;

def stepIncrease():
    global step
    step += 1

def stepDisplay(message):
    global step
    display = "\t%s" % (message)
    spaces = 70 - len(display)
    print display,
    print spaces * '.',
    step += 1

def stepFail():
    print 'failed'
    exit(0);

def stepSuccess(msg='success'):
    print msg

def deviceCapabilities(t, src, dst):
      global port
      spath = '/ncs:devices/device{"' + src + '"}'
      dpath = '/ncs:devices/device{"' + dst + '"}'
      
      cspath = spath + '/capability'
      dspath = dpath + '/capability'
      mspath = spath + '/module'
      mdpath = dpath + '/module'
      with t.cursor(cspath) as caps :
         for cap in caps :
           capability = str(cap[0])
           cp = cspath + '{"' + capability + '"}'
           dp = dspath + '{"' + capability + '"}'
           revision = "none"
           module = "none"
           if (t.exists(cp  + "/revision")) :
               revision = t.get_elem(cp + "/revision");
           if (t.exists(cp + "/module")) :
               module = t.get_elem(cp + "/module");
               msp = mspath + '{"' + str(module) + '"}'
               mdp = mdpath + '{"' + str(module) + '"}'
               if (t.exists(msp)) :
                  if not (t.exists(mdp)) :
                     t.create(mdp)
                  if not (revision == 'none') :
                     t.set_elem(revision, mdp + "/revision")

               if not (t.exists(dp)) :
                 t.create(dp)
                 if not (revision == 'none') :
                    t.set_elem(revision, dp + "/revision")
                 if not (module == 'none') :
                    t.set_elem(module, dp + "/module")
             
      return True

def main(argv):
    global services
    global port
    global devcfg
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
    parser.add_argument("-f", "--from-device", action='store', dest='src', help="Juniper device to migrate from")
    parser.add_argument("-v", "--verbose", action='store_true', dest='verbose', help="verbose")
    parser.add_argument("-n", "--name", action='store', dest='name', help="Don't commit any changes")
    parser.add_argument("-d", "--dcount", action='store', dest='count', help="# of devices to replicate")

    args = parser.parse_args()

    if args.command:
        print_ncs_command_details()
        exit(0)

    print "\nStarting device clone from device [%s] ....\n" % (args.src) 
    print "\tCreating %s device(s)\n" % (args.count)

    port = int(os.getenv('NCS_IPC_PORT', _ncs.NCS_PORT))
    maapi.util._overrideProductPort = port
    t = maapi.scripts.attach_and_trans()

    # First verify source device exist(s)
    if devExists(t,args.src) == False:
      print "Source device [%s] doesn't exist" % (args.src)
    
    devcfg = runCliCommand("show devices device %s | display xml" % (args.src))

    dev=1
    success=0
    th=0
    s = None

    while dev != (int(args.count) + 1):
       
       trans_id = int(os.getenv('NCS_MAAPI_THANDLE', 0))

       if success == 0:

          s = socket.socket()
          _ncs.maapi.connect(s, '127.0.0.1', port)

          _ncs.maapi.start_user_session(s, 'admin',
                                        'device-replicate', [], '127.0.0.1',
                                         _ncs.PROTO_TCP)

          th = _ncs.maapi.start_trans(s, _ncs.RUNNING, _ncs.READ_WRITE)
          success += 1

       dst = "%s_%s" % (args.name, dev)
       if devExists(t, dst) == False:
          stepDisplay("Cloning device %s " % (dst))
          copyDevice(th, s, args.src, dst)
          deviceCapabilities(th, args.src, dst)
          stepSuccess()
          success += 1
       else:
         stepIncrease()
       dev += 1
       if success == 10:
         print "\n\tExecuting commit operation...saving changes\n"
         _ncs.maapi.apply_trans_flags(s, th, keepopen=1, flags=NO_NETWORKING)
         success = 0
         th = 0
    if th:
       print "\n\tExecuting final commit operation...saving changes\n"
       _ncs.maapi.apply_trans_flags(s, th, keepopen=0, flags=NO_NETWORKING)
       _ncs.maapi.finish_trans(s, th)
       _ncs.maapi.end_user_session(s)    

    print "\nCompleted device cloning migration from device [%s]\n" % (args.src) 
    print " "
if __name__ == '__main__':
    main(sys.argv[1:])
