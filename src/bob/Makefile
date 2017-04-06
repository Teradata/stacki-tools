# @SI_Copyright@
# @SI_Copyright@

PKGROOT		= /opt/stack
ROLLROOT	= ../..
DEPENDS.FILES	= pallet_builder.py
DEPENDS.DIRS	= playbooks

include $(STACKBUILD)/etc/CCRules.mk


build:
	echo "Building ... "

install::
	mkdir   -p -m 755                           $(ROOT)/$(PKGROOT)/bin/
	$(INSTALL) -m 0755 pallet_builder.py        $(ROOT)/$(PKGROOT)/bin/
	mkdir   -p -m 755                           $(ROOT)/etc/profile.d
	$(INSTALL) -m 0755 share/motd.sh            $(ROOT)/etc/profile.d/
	mkdir   -p -m 755                           $(ROOT)/$(PKGROOT)/share/stacki-bob/
	$(INSTALL) -m 0644 share/sample.ini         $(ROOT)/$(PKGROOT)/share/stacki-bob/
	$(INSTALL) -m 0644 share/style.css          $(ROOT)/$(PKGROOT)/share/stacki-bob/
	$(INSTALL) -m 0644 share/index.html         $(ROOT)/$(PKGROOT)/share/stacki-bob/
	$(INSTALL) -m 0644 share/buildserver.conf   $(ROOT)/$(PKGROOT)/share/stacki-bob/
	$(INSTALL) -m 0644 playbooks/*              $(ROOT)/$(PKGROOT)/share/stacki-bob/
	mkdir   -p -m 755                           $(ROOT)/export/build/vars
	mkdir   -p -m 755                           $(ROOT)/export/nightly
	mkdir   -p -m 755                           $(ROOT)/export/src
