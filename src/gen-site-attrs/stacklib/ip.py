#! /usr/bin/python


class ipaddress(object):
	''' ipaddress handles the logic of calculating IP host information, storing the decimal value of the IP address under the hood '''

	def __init__(self, addr, netmask = None):
		''' valid argument formats:
		    (a.b.c.d, w.x.y.z)
		    (a.b.c.d/n)
		    (a.b.c.d/w.x.y.z)
		'''

		self._address = None
		self._subnet_mask = None

		if not addr:
			raise ValueError("address must be specified")

		# if netmask is None, check for cidr-notation in 'addr'
		if not netmask:
			try:
				addr, netmask = addr.split('/')
			except ValueError:
				raise ValueError("netmask must be specified")

		# assign the values
		self.address = addr
		self.subnet_mask = netmask

	@property
	def address(self):
		return decimal_ip_to_string(self._address)

	@address.setter
	def address(self, addr):
		if isinstance(addr, int):
			self._address = addr
		else:
			# convert from dotted-quad string
			self._address = decimal_ip_from_string(addr)

	@property
	def subnet_mask(self):
		return decimal_ip_to_string(self._subnet_mask)

	@subnet_mask.setter
	def subnet_mask(self, netmask):
		''' netmask could be cidr notation or dotted-quad '''
		try:
			netmask = int(netmask.replace('/', ''))
			if 1 <= netmask <= 31:
				self._subnet_mask = cidr_to_netmask(netmask)
		except ValueError:
			# if it isn't cidr, try 'dotted-quad'-style next.
			self._subnet_mask = decimal_ip_from_string(netmask)

	@property
	def cidr(self):
		''' the number of bits in the network portion of the subnet '''
		return str(netmask_to_cidr(self._subnet_mask))

	@property
	def network(self):
		return decimal_ip_to_string(self._get_network())

	def _get_network(self):
		''' AND the host address and the subnet mask '''
		return self._address & self._subnet_mask

	@property
	def broadcast(self):
		return decimal_ip_to_string(self._get_broadcast())

	def _get_broadcast(self):
		''' OR the network and the inverse of the subnet_mask '''
		return self._get_network() | ~self._subnet_mask

	@property
	def gateway(self):
		''' return the first potential host in the network '''
		return decimal_ip_to_string(self._get_gateway())

	def _get_gateway(self):
		# this is obviously not always true.
		return self._get_network() +1


def netmask_to_cidr(netmask):
	''' return the number of bits in the (decimal) netmask '''

	cidr = 0
	try:
		cidr = bin(netmask).count('1')
	except TypeError:
		for octet in netmask.split('.'):
			cidr += sum([bin(int(octet)).count('1')])
	return cidr


def cidr_to_netmask(cidr):
	''' return a decimal representing the netmask '''

	return 0xffffffff ^ (1 << 32 - cidr) -1

def decimal_ip_from_string(addr):
	address = 0
	for i, octet in enumerate(map(int, addr.split('.'))):
		address += octet << (8 * (3-i))
	return address

def decimal_ip_to_string(addr):
	return '.'.join((str(addr >> i & 0xff) for i in [24,16,8,0]))

if __name__ == "__main__":
	arg_tups = [
		('192.168.1.10', '255.255.255.0'),
		('10.0.1.242', '/28'),
		('10.0.1.242', '255.0.0.0'),
		('172.16.3.27/16', None),
		('8.8.8.8', '/8'),
		('10.37.18.242', '/12'),
		]
	for tup in arg_tups:
		i = ipaddress(*tup)
		print(i.address, i.subnet_mask, i.network, i.broadcast, i.cidr, i.gateway)


