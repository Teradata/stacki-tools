#
# @SI_Copyright@
# @SI_Copyright@
#

import sys
import stack.api as api
import stack.commands
import os.path
from stack.exception import *
from stack.commands.sync.host import Parallel
from stack.commands.sync.host import timeout


class Command(stack.commands.sync.host.command):
	"""
	Sync an arbitrary file to backend nodes.
	
	<param type='string' name='src' optional='0'>
        </param>

	<param type='string' name='dest' optional='0'>
        </param>

	<param type='string' name='service'>
	Service to restart if you've added a service
	related file.
	</param>
	
	
	<example cmd='sync host file src=/etc/motd dest=/tmp'>
	Giving no hostname or regex will sync
        to all backend nodes by default.
	</example>

	<example cmd='sync host file src=./docker.config 
		dest=/etc/sysconfig/docker service=docker'>
	Sync docker config and restart service
	</example>
	"""

	def run(self, params, args):
		src,dest,svc = self.fillParams([
                        ('src', None),
                        ('dest', None),
                        ('service', None)
                        ])

		recurse = False

		hosts = self.getHostnames(args, managed_only=1)
		me = self.db.getHostname('localhost')

				
		if not src:
			raise ParamError(self,'src', "- no source is given.")

		if not os.path.isfile(src):
			if os.path.isdir(src):
				recurse = True
			else:
				raise CommandError(self, '%s is not a file or a directory' % src)

		if not dest:
			raise ParamError(self,'dest', "- no destination is given.")
			
		threads = []
		for host in hosts:
			if me != host:
				if recurse:
					cmd = 'scp -r %s %s:%s ' % (host,src,dest)
				else:
					cmd = 'scp %s %s:%s ' % (host,src,dest)

			cmd += 'bash > /dev/null 2>&1 '

			try:
				p = Parallel(cmd)
				p.start()
				threads.append(p)
			except:
				pass

		#
		# collect the threads
		#
		for thread in threads:
			thread.join(timeout)

		if svc:
			cmd = 'systemctl daemon-reload'
			cmd += 'systemctl restart %s' % svc
			api.Call('run.host',[hosts, cmd])
