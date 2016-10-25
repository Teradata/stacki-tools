# Stacki Tools

This repository contains code that runs outside of a Stacki frontend, that is,
a Stacki frontend is not required to run any code in this repo.
This repo contains:

- `stacki-tools/src/fab`
Used to create `stacki-fab` RPM which contains
`/opt/stack/bin/frontend_install.py`.
This program is used to transform a server that is running vanilla CentOS
(or Red Hat) into a working Stacki frontend.
See below for details.

- `stacki-tools/src/gen-site-attrs`
Used to create `stacki-gen-site-attrs` RPM which contains
`/opt/stack/bin/stacki_attrs.py`.
This program is used to create `/tmp/site.attrs` that can be used with Packer to
automate the installation of a Vagrant/VirtualBox based frontend.
See below for details

---

# `stacki-tools/src/fab`

---

# `stacki-tools/src/gen-site-attrs`

stacki_attrs.py is a python script to generate a stacki `site.attrs` file for use in provisioning a Stacki Frontend.

stacki_attrs.py allows you to specify all of the possible variables that normally go into a `site.attrs` file, which you can then roll into an install ISO or (better) serve from an HTTP server (or whatever python's urllib can handle) from a newer version of StackiOS.

stacki_attrs.py has built in defaults for each option.  Simply run `/opt/stack/gen-site-attrs/bin/stacki_attrs.py list` to see what those are.  Aside from the defaults, stacki_attrs.py does some sanity checking on your input (checks IP address and timezone validity, etc).  Options can be specified with the shortest distinct name e.g. `--g` and `--gateway` are synonomous, but `--net` is invalid because it could be `--network` or `--netmask`.  Running `stacki_attrs.py list` will display any specified options as an overlay on top of the defaults.

## Misc

### Security

You specify your password in plaintext, and then write it out to disk in a variety of encrypted formats.  You should really just change the password once the system is up and running.  `stack set password` is your friend here.

### Networking

stacki_attrs.py will attempt to calculate your various networking attributes based on IP and netmask (if provided), but will also defer to and options specified on the command-line, even if it thinks they're wrong.

### Timezones

For a list of valid timezones, run something like: `python -c "import pytz; from pprint import pprint; pprint(pytz.all_timezones)" | less`.  It currently defaults to the West Coast US timezone, which as we all know, is the Best Coast.
