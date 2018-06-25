# -*- mode: python; python-indent: 4 -*-
import ncs
import _ncs
from ncs.application import Service
import ncs.template
import ncs.maagic as maagic
import ncs.maapi as maapi
import ncs.template
import re
import os
from ncs.dp import Action
from ncs.application import Application

NO_NETWORKING = ( 1 << 4)

########################################################
# Reconcile Action Handler
########################################################
class ActionHandler(Action):
    """This class implements the Reconcile Action class."""

    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):

        results = re.search('\{(.*)\}', str(kp))
        sni = results.group(1)
        self.log.info("Reconcile VRF Service Instance [%s]" % (sni))
        output.status = 'success'

        # Check environment setting for IPC port value
        port = int(os.getenv('NCS_IPC_PORT', _ncs.NCS_PORT))
        self.log.info("Using NCS IPC port value [%d]" % (port))

        try:
          with maapi.Maapi("127.0.0.1", port, path=None) as self.maapi:
            self.maapi.start_user_session("admin", 'VRF-REC-'+ sni , [])
            with self.maapi.start_write_trans(db=ncs.RUNNING) as t:
               root = maagic.get_root(t, shared=False)
               sn = root.vrf__vrf[sni]
               ###
               # Apply the reconcile template
               ###
               self.template = ncs.template.Template(sn)
               self.vars = ncs.template.Variables()
               self.template.apply('vrf-oob-reconcile', self.vars)
               ###
               # Eexecute dry run to check if the reconcile was successful
               ###
               dryRun = root.ncs__services.commit_dry_run
               inp = dryRun.get_input()
               result = dryRun(inp)
               ###
               # Any device/network changes mean something outside of what we can reconile
               # has changed and we will fail the reconcile operation
               ###
               if (result.cli) and (result.cli.local_node.data):
                 self.log.debug("oob-reconile[%s] dry-run results: [%s]" % (sni,result.cli.local_node.data))
                 m = re.search(r'^ devices {\n     device ', 
                               result.cli.local_node.data, 
                               re.MULTILINE)
                 
                 if (m):
                    self.log.error('oob-reconcile [%s] failed' % (sni))
                    output.status = 'failed'
                    output.error_message = result.cli.local_node.data 
               else:
                  ###
                  # No output from commit dry-run, we need to check re-deploy to make
                  # sure there aren't any unreconcilable changes in the CDB
                  ###
                  self.log.debug("oob-reconile[%s] starting re-deploy dry-run" % (sni))
                  redeploy = sn.re_deploy
                  inp = redeploy.get_input()
                  inp.dry_run.create()
                  result = redeploy(inp)
                  if (result.cli) and (result.cli.local_node.data):
                     self.log.debug("oob-reconile[%s] re-deploy dry-run results: [%s]" % (sni,result.cli.local_node.data))
                     output.status = 'failed'
                     output.error_message = result.cli.local_node.data 

               if (output.status != "failed"):
                 self.log.info("oob-reconcile[%s]:Saving/Applying reconile changes" % (sni))
                 t.apply()
   
        except Exception as e:
           output.status = 'failed'
           output.error_message = "Failure during reconcillation processing"
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
