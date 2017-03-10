#! /usr/bin/env python

'''Generate a site.attrs file to prepare for an unattended installation of a Stacki Frontend.  

Usage:
  stacki_attrs.py list [options]
  stacki_attrs.py [options]

Options:
  -h --help                         Display usage.
  --debug                           Print various data structures during runtime
  --template=<template filename>    Location of site.attrs.j2
  --output_filename=<filename>      Location to save site.attrs
  --stdout                          Instead of saving the file, print it to stdout
  --fqdn=<fqdn>                     FQDN of the frontend
  --timezone=<timezone>             Timezone string
  --network=<network address>       Network for Stacki traffic
  --ip=<ip_address>                 IP address of frontend
  --netmask=<subnet mask>           Netmask of frontend
  --cidr=<bits in netmask>          The CIDR represenation of the netmask
  --gateway=<gateway address>       Gateway of frontend
  --broadcast=<broadcast address>   Broadcast of frontend
  --interface=<interface name>      Device used for Stacki traffic
  --mac_address=<mac address>       MAC address of the interface
  --password=<root password>        Password to set for administration
  --pass_encrypted                  Indicate that the password provided is already encrypted
  --dns_servers=<server1[,server2]> DNS servers for frontend

'''

from __future__ import print_function

import sys
import os
import string
import random
import pytz
import jinja2
import socket
import hashlib
import subprocess
from pprint import pprint
from stacklib import docopt
from stacklib import ipaddress
# also requires the openssl binary installed!

default_ipv4 = {
	'ip': '192.168.42.10',
	'netmask': '255.255.255.0',
	'broadcast': '',
	'gateway': '',
	'network': '',
	'cidr': '',
	}

defaults = {
	'fqdn': 'stackifrontend.localdomain',
	'interface': 'enp0s8',
	'dns_servers': '8.8.8.8',
	'timezone': 'America/Los_Angeles',
	'password': 'password',
	'pass_encrypted': False,
	'mac_address': '08:00:d0:0d:c1:89',
	'template': '/opt/stack/gen-site-attrs/site.attrs.j2',
	'output_filename': './site.attrs',
	}

class Attr():
	''' Attr represents the logic for creating a valid site.attrs file based on `settings`. '''

	# the basic attributes we'll need to set or generate
	attr_keys = [
		'hostname',
		'domain',
		'interface',
		'network',
		'ip',
		'netmask',
		'cidr',
		'broadcast',
		'gateway',
		'dns_servers',
		'timezone',
		'password',
		'mac_address',
		'shadow_pass',
		]

	def __init__(self, settings):
		''' build the object from `settings` '''

		self.attrs = dict.fromkeys(Attr.attr_keys)
		self.settings = settings
		ipv4_settings = dict((k, self.settings[k]) for k in default_ipv4)
		try:
			self.set_timezone()
			self.set_fqdn()
			self.set_ethernet_dev()
			self.set_mac_address()
			for addr, value in ipv4_settings.items():
				self.set_address(addr, value)
			self.set_dns()
			self.set_password()
			self.render_attrs_file(settings['template'])
		except ValueError as e:
			raise

	def render_attrs_file(self, template_file):
		''' Render the stored attributes as a 'site.attrs', using template `template_file` '''

		if not os.path.isfile(template_file):
			template_file = './site.attrs.j2'

		with open(template_file) as template:
			rendered_attrs_file = jinja2.Template(template.read()).render({
				'HOSTNAME': self.attrs['hostname'],
				'DOMAIN': self.attrs['domain'],
				'BACKEND_NETWORK_INTERFACE': self.attrs['interface'],
				'BACKEND_NETWORK': self.attrs['network'],
				'BACKEND_NETWORK_ADDRESS': self.attrs['ip'],
				'BACKEND_NETMASK': self.attrs['netmask'],
				'BACKEND_NETMASK_CIDR': self.attrs['cidr'],
				'BACKEND_BROADCAST_ADDRESS': self.attrs['broadcast'],
				'BACKEND_MAC_ADDRESS': self.attrs['mac_address'],
				'GATEWAY': self.attrs['gateway'],
				'DNS_SERVERS': self.attrs['dns_servers'],
				'TIMEZONE': self.attrs['timezone'],
				'SHADOW_PASSWORD': self.attrs['shadow_pass'],
			})

		self.output = rendered_attrs_file + '\n'

	def set_timezone(self):
		''' try to fit the timezone to a list of actual timezones '''

		timezone = self.settings['timezone']
		try:
			pytz.timezone(timezone)
		except pytz.exceptions.UnknownTimeZoneError:
			raise ValueError('Error: Could not validate timezone, "%s"' % timezone)
		self.attrs['timezone'] = timezone

	def set_fqdn(self):
		''' try to split a fqdn into host and domain '''

		fqdn = self.settings['fqdn']
		# split, assign, look for valueerror
		try:
			host, domain = fqdn.split('.', 1)
		except ValueError as e:
			raise ValueError('Error: "%s" is not a fully-qualified domain name' % fqdn)
		self.attrs['hostname'] = host
		self.attrs['domain'] = domain

	def set_ethernet_dev(self):
		''' ethernet device names are weird -- just check that it isn't empty '''

		device = self.settings['interface']
		if not device:
			raise ValueError('Error: ethernet device name must not be empty')
		self.attrs['interface'] = device

	def set_mac_address(self):
		''' try to parse the MAC in a few different formats '''

		mac_addr = self.settings['mac_address']
		if mac_addr.count(':') == 0 and len(mac_addr) == 12:
			mac_addr = ':'.join(s.encode('hex') for s in mac_addr.decode('hex'))
		elif mac_addr.count(':') == 5 and len(mac_addr) == 17:
			# this is the format we want it in...
			pass
		else:
			raise ValueError('Error: MAC address must either be 12 hex digits or 6 hexdigit pairs separated by colons')
		self.attrs['mac_address'] = mac_addr

	def set_address(self, key, address):
		''' check that the address is a valid addressable ipv4 address '''

		if key == 'cidr':
			self.attrs[key] = address
			return

		if len(address.split('.')) != 4:
			raise ValueError('Error: addresses must be specified in dotted-quad format: "%s"' % address)
		try:
			socket.inet_aton(address)
		except socket.error as e:
			raise ValueError('Error: "%s" is not a valid ipv4 address' % address)
		# filter the ip through socket.inet_* to ensure legibility
		self.attrs[key] = socket.inet_ntoa(socket.inet_aton(address))

	def set_dns(self):
		''' split string across commas, if any, and check the ip is valid '''

		dns = self.settings['dns_servers']
		valid_dns_servers = []
		for address in dns.split(','):
			if len(address.split('.')) != 4:
				raise ValueError('Error: addresses must be specified in dotted-quad format: "%s"' % address)
			try:
				socket.inet_aton(address.strip())
			except socket.error as e:
				raise ValueError('Error: "%s" is not a valid ipv4 address' % address)
			valid_dns_servers.append(socket.inet_ntoa(socket.inet_aton(address.strip())))
		# filter the ip through socket.inet_* to get something legible
		self.attrs['dns_servers'] = ','.join(valid_dns_servers)

	def set_password(self):
		''' encrypt the password in the 'crypt' format '''

		password = self.settings['password']
		if not password:
			raise ValueError('Error: password must not be empty')

		# PrivateRootPassword
		# can't rely on MacOSX underlying C crypt() code
		if not self.settings['pass_encrypted']:
			openssl_cmd = 'openssl passwd -1 -salt %s %s' % (gen_salt(), password)
			encrypted_pass = subprocess.check_output(openssl_cmd.split()).strip()
		else:
			encrypted_pass = password
		self.attrs['shadow_pass'] = encrypted_pass


def gen_salt():
	''' generate a best-effort random salt '''

	# base list of characters, note len()==64
	chars = string.ascii_letters + string.digits + './'
	salt = ''
	# generate a urandom byte, modulo it by len(chars), use result as index to pick char, append to salt
	for i in range(0,8):
		salt += chars[ord(os.urandom(1)) % len(chars)]
	return salt


if __name__ == '__main__':
	arguments = docopt.docopt(__doc__)
	# prune out the '--'s
	cleaned_args = dict((k.replace('--',''), v) for (k,v) in arguments.iteritems())

	debug_flag = False
	if cleaned_args['debug']:
		del cleaned_args['debug']
		debug_flag = True

	# print_debug is literally noop if --debug was not passed
	print_debug = print if debug_flag else lambda *a, **k: None

	print_debug('cleaned_args', cleaned_args)

	settings = defaults.copy()
	settings.update(default_ipv4)

	# grab only the ipv4 values, using 'default_ipv4' for the keys
	user_ipv4_settings = dict((k, cleaned_args[k]) for k in default_ipv4)
	print_debug('user ipv4 settings: ', user_ipv4_settings)

	# overlay only the options actually specified
	cleaned_args = dict((k, v) for (k,v) in cleaned_args.iteritems() if v)
	print_debug('cleaned_args without Nones', cleaned_args)
	settings.update(cleaned_args)
	print_debug('combined settings', settings)

	ip_addr = user_ipv4_settings['ip']
	mask = user_ipv4_settings['netmask']
	cidr = user_ipv4_settings['cidr']
	if not cidr and not mask and ip_addr and '/' in ip_addr:
		settings['ip'], mask = ip_addr.split('/')
		if len(mask) > 2 and '.' in mask:
			settings['netmask'] = mask
		else:
			settings['cidr'] = mask
	elif ip_addr and mask:
		# if they pass both, that's fine
		pass
	elif ip_addr and cidr:
		pass
	elif not ip_addr and not mask:
		# if they pass neither, they get the defaults
		pass
	else:
		# but if they pass one but not the other...
		print('Error: if specifying one, you must specify both ip as well as netmask or cidr')
		sys.exit(1)

	if mask:
		ipstring = unicode(settings['ip'] + '/' + mask)
	elif cidr:
		ipstring = unicode(settings['ip'] + '/' + cidr)

	ip_addr = ipaddress.IPv4Network(ipstring, strict=False)

	settings['netmask']         = str(ip_addr.with_netmask).split('/')[1]
	settings['cidr']            = str(ip_addr.prefixlen)

	# calulate these only if the user didn't specify
	if not user_ipv4_settings['network']:
		settings['network']         = str(ip_addr.network_address)
	# assume the gateway is the first host IP in the network
	if not user_ipv4_settings['gateway']:
		settings['gateway']         = str(ip_addr[1])
	if not user_ipv4_settings['broadcast']:
		settings['broadcast']       = str(ip_addr.broadcast_address)

	# for 'list', pretty print the defaults overlayed with user args
	if cleaned_args.has_key('list'):
		del settings['list']
		pprint(settings)
		sys.exit(0)

	# Actually attempt to set the attributes
	try:
		attrs = Attr(settings)
	except ValueError as e:
		print(e)
		sys.exit(1)

	print_debug('compiled attributes', attrs.attrs)

	# and finally, render the file and save to disk
	if cleaned_args.has_key('stdout'):
		print(attrs.output)
	else:
		filename = settings['output_filename']
		if os.path.isdir(filename):
			filename = filename + '/' + os.path.basename(defaults['output_filename'])

		with open(filename, 'wb') as outfile:
			outfile.write(attrs.output)
	sys.exit(0)

