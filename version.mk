export ROLL		= stacki-tools
COMMIT			= $(shell git rev-parse --short HEAD)
export ROLLVERSION	= 5.0_$(shell date +\%Y\%m\%d)_$(COMMIT)
COLOR			= pink
export RELEASE		= $(shell $(STACKBUILD.ABSOLUTE)/bin/os-release)
