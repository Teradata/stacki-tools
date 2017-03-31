# @SI_Copyright@
# @SI_Copyright@

PKGROOT         = /opt/stack
ROLLROOT	= ../..

include $(STACKBUILD)/etc/CCRules.mk

build::

install::
	mkdir -p $(ROOT)$(PKGROOT)
	mkdir -p $(ROOT)/$(PY.STACK)/stack/commands/
	find -name "*.py" | \
		cpio -pduv $(ROOT)/$(PY.STACK)/stack/commands/
	find $(ROOT)/$(PY.STACK)/stack/commands -name "*.py" | awk \
		'{ print "\nRollName = \"$(ROLL)\"" >> $$1; }'
	find $(ROOT) -type d -exec chmod a+rx {} \;

clean::
