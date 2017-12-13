export ROLL		= stacki-tools
export ROLLVERSION	= 5.0_`date +\%Y\%m\%d`_`git rev-parse --short HEAD`
COLOR			= pink
export RELEASE		= $(shell $(STACKBUILD.ABSOLUTE)/bin/os-release)
