# This is the documentation for Stacki B.O.B. (Bot-Operated Builds)

```
      ____  _             _    _ 
     / ___|| |_ __ _  ___| | _(_)
     \___ \| __/ _` |/ __| |/ / |
      ___) | || (_| | (__|   <| |
     |____/ \__\__,_|\___|_|\_\_|
          ____   ___   ____      
         | __ ) / _ \ | __ )     
         |  _ \| | | ||  _ \     
         | |_) | |_| || |_) |    
         |____(_)___(_)____(_)


         Bot-Operated Builds

```

BOB is a system for simplfying and automating the process of building Stacki as well as any Stacki Pallet, directly from source.  While building Stacki from source has gotten *much* easier in recent years, it is still non-trivial.  BOB is very useful internally for producing nightly builds, but could also be useful to the Stacki community at large, whether you'd like to:

* contribute to the development of Stacki itself
* build your own pallets for the community at large or internally for your organization
* to live on the edge and test new features


---

## Requirements
*Stacki pallets must be built on a Stacki Frontend, but this should not be a Frontend used in production!*  In an ideal situation you would have one VM which is coordinating builds, and a number of VM's which it can farm out builds jobs to, though this isn't strictly necessary.  Included in this repo are some ansible playbooks which handle building some of our more unusual pallets and which have different build requirements.  Obviously to use these you'll need Ansible >2.0 installed on the BOB server.

## Setup
Running 'make' in this repo will produce an RPM suitable to install on a Stacki Frontend.  Install the RPM on the Stacki Frontend.  By default, BOB will place a script in /etc/profile.d/motd.sh which contains information about the builds.

If you would like build artifacts available via HTTP, make a series of symbolic links like so:

```
ln -s /export/nightly /var/www/html/nightly 
ln -s /opt/stack/share/stacki-bob/style.css /var/www/html/style.css
ln -s /opt/stack/share/stacki-bob/index.html /var/www/html/index.html
ln -s /opt/stack/share/stacki-bob/buildserver.conf /etc/httpd/conf.d/stacki-bob.conf
systemctl restart httpd
stack add host firewall frontend network=all service="www" protocol="tcp" chain="INPUT" action="ACCEPT" rulename="bob-www"
stack sync host firewall localhost restart=true
```

Then point your webbrowser to your Stacki-BOB server and you'll be redirected to your build artifact directory.

## Usage
From here, in the simplest case you can add a cron job to point `pallet_builder.py` at an ini file describing the build parameters, and you're done.  See `/opt/stack/share/stacki-bob/sample.ini` for an example.  In the future, we may include these build files in our pallet repositories.  If you're pointing at a private GitHub repository, you'll need to provide an access token.

For a more involved setup, you can set up a few more VM's, and use the `do_build.yml` ansible playbook to specify which builds to do on which servers, with which ini files.  At the end of `do_build.yml`, the build artifacts are copied back to the BOB server under `/export/nightly/`, and the build slave is cleaned up.

## TODO
There's a lot of work that could be done here but feature-wise, it does everything it needs to do.  Most of this was written while working through a testing cycle ahead of a major release of Stacki, so there's a few rough edges, and more documentation that should be written.  A 'better' job scheduler than cron could be used, and we could also tie into GitHub's hooks to create a queue of build jobs whenever there's a commit, rather than relying on periodic jobs.
