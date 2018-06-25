# -*- mode: python; python-indent: 4 -*-
import ncs
import _ncs
from ncs.application import Service
import ncs.template
import ncs.maagic as maagic
import ncs.maapi as maapi
import re
import threading

from ncs.dp import Action
from ncs.application import Application

########################################################
# Worker thread for reconcile
########################################################
def reconcileWorker(lsa_node, name, self, res):
     with ncs.maapi.single_write_trans('admin', 'VRF-REC-' + lsa_node) as t:
       root = maagic.get_root(t, shared=False)
       lsan = root.ncs__devices.device[lsa_node]
       res['status'] = 'success'
       self.log.debug("    starting reconcile [%s] LSA node [%s]" % (name, lsa_node))
       try:
         action = lsan.config.vrf__vrf[name].oob_reconcile
         inp = action.get_input()
         opt = action(inp)
         self.log.debug("     vrf[%s] LSA Node [%s] reconcile successfully completed" % (name, lsa_node))
         if opt.status == 'failed':
            self.log.error("     vrf[%s] LSA Node [%s] reconcile failed [%s]" % (name, lsa_node, opt.error_message))
            res['status'] = 'failed'
            res['message'] = 'LSA Node [%s] failure details \n%s\n' % (lsa_node,opt.error_message)

       
       except Exception as e:
          res['status'] = 'failed'
          res['message'] = 'vrf[%s] error during reconcile for LSA Node [%s]' % (name, lsa_node)
          self.log.error(e)

########################################################
# Worker thread for sync-from
########################################################
def syncWorker(lsa_node, name, self, res):

     with ncs.maapi.single_write_trans('admin', 'VRF-REC-' + lsa_node) as t:
        root = maagic.get_root(t, shared=False)
        lsan = root.ncs__devices.device[lsa_node]
                  
        try:
          self.log.debug('     vrf reconcile lsa-node [%s] sync-from starting' % (lsa_node))
          syncFrom = lsan.sync_from
          inp = syncFrom.get_input()
          output = syncFrom(inp)

          if output.result == True:
            self.log.debug('    vrf reconcile lsa-node [%s] sync-from completed' % (lsa_node))
          else:
            self.log.info('    vrf reconcile lsa-node [%s] sync-from Failure' % (lsa_node))

        except Exception as e:
          res['status'] = 'failed'
          res['message'] = 'Exeception occurred during sync-from processing !'
          self.log.error(e)

########################################################
# Action Handler
########################################################
class ActionHandler(Action):
    """This class implements the Reconcile Action class."""

    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):

        results = re.search('\{(.*)\}', str(kp))
        sni = results.group(1)
        self.log.info("VRF Service Instance [%s]" % (sni))
        output.status = 'success'
        error_message = ''
       
        try:
          with ncs.maapi.single_write_trans('admin', 'OOB-REC-' + sni) as t:

             self.root = maagic.get_root(t, shared=False)
            
             ###
             # Retreive service instance form keypath
             ###
             sn = self.root.ncs__services.vrf[sni]

             ###
             # Step(1): Issue the LSA Node reconcile actions
             ###
             self.log.debug("Step(1): vrf [%s] LSA node reconcile starting..." % (sni))
             threads = {}
             for dn in sn.device_list:
                 threads[dn] = {}
                 thr = threading.Thread(target=reconcileWorker, args=(dn, sni, self, threads[dn]))
                 threads[dn]['thread'] = thr
                 thr.start()
             for dn in sn.device_list:
                 threads[dn]['thread'].join()

             for dn in sn.device_list:
                 self.log.debug('    LSA Node [%s] reconcile result status [%s]' % (dn, threads[dn]['status']))
             self.log.debug("Step(1): vrf [%s] LSA node reconcile completed" % (sni))

             ###
             # Step(2): Issue sync-from actions to each LSA node
             ###
             self.log.debug("Step(2): vrf [%s] LSA node sync-from starting..." % (sni))
             sthreads = {}
             for dn in sn.device_list:
                 sthreads[dn] = {}
                 thr = threading.Thread(target=syncWorker, args=(dn, sni, self, sthreads[dn]))
                 sthreads[dn]['thread'] = thr
                 thr.start()
             for dn in sn.device_list:
                 sthreads[dn]['thread'].join()
             self.log.debug("Step(2): vrf [%s] LSA node sync-from completed" % (sni))

             ###
             # Step(3): Apply the top level reconcilliation template
             ###
             self.log.debug("Step(3): vrf [%s] Service node reconcile starting..." % (sni))
             for dn in sn.device_list:
               device = self.root.ncs__devices.ncs__device[dn].config.vrf__vrf[sni]            
               self.template = ncs.template.Template(device)
               self.vars = ncs.template.Variables()
               self.vars.add('VRF', sni)
               self.vars.add('LSAN', dn)
               self.log.debug("Step(3): LSA NODE [%s] Applying template..." % (dn))
               self.template.apply('vrf-oob-reconcile', self.vars)
             self.log.debug("Step(3): vrf [%s] Service node reconcile completed" % (sni))

             ###
             # Step(4): Commit transaction for top level reconcile
             ###
             t.apply()

             ###
             # Evalute the results for all of involved NSO LSA nodes
             ###
             for dn in sn.device_list:
                if threads[dn]['status'] == 'failed':
                   output.status = 'failed'
                   error_message += threads[dn]['message']
                   output.error_message = error_message

             self.log.debug("Step(4): vrf [%s] reconcile returning status[%s]" % (sni, output.status))

        except Exception as e:
           self.log.error("vrf reconcile operation for instance [%s] failed" %(sni))
           output.status = 'failed'
           output.error_message = 'Exception executing reconcile operation'
           self.log.error(e)


        return ncs.CONFD_OK

########################################################
# NSO Action Registration
########################################################
class ServiceActions(ncs.application.Application):
    def setup(self):
       
        self.log.info('OOB Reconcile Action(s) Registering')
        self.register_action('vrf-reconcile-point', ActionHandler, [])
        self.log.info('OOB Reconcile Action(s) Registration Completed...')

    def teardown(self):

        self.log.info('Actions FINISHED')
