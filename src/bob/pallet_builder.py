#! /usr/bin/python

from __future__ import print_function

import os
import sys
import glob
import shutil
import subprocess
from collections import namedtuple
import re
from functools import partial
import ConfigParser

ExecResults = namedtuple('ExecResults', ['stdout', 'stderr', 'exit_status'])

GLOBAL_BUILD_LOG = '/export/nightly/build_log.txt'

def exec_cmd(command, obfuscate = None):
    """
    Run shell command, return namedtuple with output and exit status.
    obfuscate is a callable if you wish to log something other than
    the exact command (to protect passwords, etc)
    """
    # if we aren't obfuscating the command, run it through str to effectively 'noop'
    # note that this obviously won't avoid it showing up in the output of `ps`
    if not obfuscate:
        obfuscate = str
    print(obfuscate(' '.join(command)))
    log('/export/nightly/build_log.txt', obfuscate(' '.join(command)))
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    output, err = proc.communicate()

    return ExecResults(output, err, proc.returncode)

def log(logfile, message):
    with open(logfile, 'a') as logfh:
        logfh.write(message + '\n')

def git_clone(url, username = None, password = None):
    # we want to obfuscate potential passwords from the logs, if they exist
    obfs = None
    if username and password:
        url = 'https://{0}:{1}@{2}'.format(username, password, url)
        # obfs is a partial lambda that replaces a username and password with plaintext tokens
        obfs = partial(
            lambda username, password, url: url.replace(username, 'USERNAME').replace(password, 'PASSWORD'),
            username,
            password)
    results = exec_cmd('git clone {0}'.format(url).split(), obfs)
    if results.exit_status:
        log('/export/nightly/build_log.txt', 'git clone failed')

def git_pull():
    results = exec_cmd('git pull'.split())
    if results.exit_status:
        log('/export/nightly/build_log.txt', 'git pull failed')

def git_get_current_commit_id():
    results = exec_cmd('git rev-parse --short HEAD'.split())
    if results.exit_status:
        log('/export/nightly/build_log.txt', 'git rev-parse failed')
    else:
        return results.stdout.strip()

def git_checkout(branch = 'master'):
    results = exec_cmd('git checkout --force {0}'.format(branch).split())
    if results.exit_status:
        log(GLOBAL_BUILD_LOG, 'git checkout failed')

def git_reset():
    results = exec_cmd('git reset --hard'.split())
    if results.exit_status:
        log(GLOBAL_BUILD_LOG, 'git reset failed')

def git_clean():
    results = exec_cmd('git clean -xfd'.split())
    if results.exit_status:
        log(GLOBAL_BUILD_LOG, 'git clean failed')


class Builder(object):
    def __init__(self, config_file):
        self.global_delivery_dir = '/export/nightly'
        self.system_build_dir = '/export/build'
        self.global_build_log = self.global_delivery_dir + '/build_log.txt'

        defaults = {
            'branch': 'master',
            'force_build': False,
            'skip_refresh': False,
            'skip_bootstrap': False,
        }

        config = ConfigParser.ConfigParser(defaults)

        try:
            config.read(config_file)
        except OSError:
            log(self.global_build_log, 'build.ini "%s" file might not exist' % config_file)
            raise
        except ConfigParser.Error as e:
            log(self.global_build_log, e)
            raise

        self.git_username = config.get('build', 'git_user')
        self.git_password = config.get('build', 'git_passwd')

        self.pallet_name = config.get('build', 'pallet_name')
        self.repo_url = config.get('build', 'repo_url')
        self.branch = config.get('build', 'branch')
        self.force_build = config.get('build', 'force_build')
        self.skip_refresh = config.get('build', 'skip_refresh')
        self.skip_bootstrap = config.get('build', 'skip_bootstrap')

        mandatory_options = (self.pallet_name, self.git_username, self.git_password, self.repo_url)
        if None in mandatory_options:
            log(self.global_build_log, 'not all args specified in build.ini file')
            raise Exception

        try:
            # check to see if password is a filename
            with open(self.git_password) as pwdfile:
                self.git_password = pwdfile.readline().strip()
        except IOError:
            # if not, assume it's the actual passwd in plaintext
            pass

        if self.repo_url.startswith('http'):
            self.repo_url.replace('https://', '')
            self.repo_url.replace('http://', '')

        if config.has_option('build', 'repo_base_dir'):
            self.repo_base_dir = config.get('build', 'repo_base_dir')
        else:
            # otherwise assume it's the same as the git repo name, which it should be
            self.repo_base_dir = self.repo_url.split('/')[-1].replace('.git', '')

        self.src_root_dir = '{0}/{1}'.format(self.system_build_dir, self.repo_base_dir)

        if config.has_option('build', 'makefile_dir'):
            self.makefile_dir = '{0}/{1}'.format(self.src_root_dir, config.get('build', 'makefile_dir'))
        else:
            self.makefile_dir = self.src_root_dir

        self.delivery_dir = '{0}/{1}'.format(self.global_delivery_dir, self.pallet_name)
        if self.branch != 'master':
            self.delivery_dir += '_{0}'.format(self.branch)
        self.logfile = '{0}/nightly-{1}-{2}-build.txt'.format(self.delivery_dir, self.pallet_name, self.branch)
        self.commit_id = ''
        self.src_version = ''


    def prepare_delivery_dir(self):
        try:
            os.mkdir(self.delivery_dir)
        except OSError:
            pass


    def refresh_git_repo(self):
        if self.skip_refresh:
            return

        # try to chdir to the repo, if it fails, we need to clone
        try:
            os.chdir(self.src_root_dir)
        except OSError:
            os.chdir(self.system_build_dir)
            git_clone(self.repo_url, self.git_username, self.git_password)

        git_pull()


    def prepare_build_dir(self):
        os.chdir(self.src_root_dir)
        if self.force_build:
            return

        git_checkout(self.branch)
        git_clean()
        git_reset()


    def pre_make(self):
        try:
            os.chdir(self.makefile_dir)
        except OSError as e:
            if e.errno == 2:
                raise

        self._set_build_env_vars()

        results = exec_cmd('make nuke.all'.split())
        if results.exit_status:
            log(self.global_build_log, 'error, make nuke.all')
            log(self.logfile, results.stdout)

        if self.skip_bootstrap:
            log(self.global_build_log, 'skipping bootstrap')
            return

        results = exec_cmd('make bootstrap'.split())
        if results.exit_status and '''make: *** No rule to make target `bootstrap'.''' in results.stdout:
            log(self.global_build_log, 'no target for make bootstrap')
        else:
            log(self.global_build_log, 'error, make bootstrap')
            log(self.logfile, results.stdout)


    def make_pallet(self):
        # clean build tree
        try:
            shutil.rmtree('{0}/build-{1}-{2}/'.format(
                self.makefile_dir, self.pallet_name, self.branch))
        except OSError as e:
            if e.errno == 2:
                pass # directory doesn't exist
            else:
                log(self.global_build_log, 'could not delete build directory')
                raise

        # make roll
        results = exec_cmd('make roll'.split())

        log(self.logfile, results.stdout)

        # exit if fail
        if results.exit_status:
            log(self.global_build_log, 'error, make roll')
            raise Exception('Error in make roll')

        if not self.make_check():
            log(self.global_build_log, 'error, make manifest-check')
            raise Exception('Error in make manifest-check')


    def deliver_iso(self):
        log(self.global_build_log, 'Copying iso to delivery directory')
        glob_str = '{0}/build-{1}-{2}/{1}-*_{3}*.iso'.format(
            self.makefile_dir, self.pallet_name, self.branch, self.commit_id)

        iso_glob = glob.glob(glob_str)
        if not len(iso_glob):
            log(self.global_build_log, 'Could not find an iso with glob: {0}'.format(glob_str))
            raise Exception('Could not find an iso with glob: {0}'.format(glob_str))
        iso_fname = iso_glob[0]

        # copy iso to delivery
        log(self.global_build_log, 'copying {0} to {1}'.format(iso_fname, self.delivery_dir))
        shutil.copy(iso_fname, self.delivery_dir)
        iso_fname = os.path.basename(iso_fname)
        iso_fpath = '{0}/{1}'.format(self.delivery_dir, os.path.basename(iso_fname))


    def make_check(self):
        results = exec_cmd('make manifest-check'.split())
        if results.exit_status:
            log(self.global_build_log, 'error, make manifest-check')
            log(self.logfile, results.stdout)
            return False
        return True


    def _set_build_env_vars(self):
        results = exec_cmd(['/bin/bash', '-c', 'source /etc/profile.d/stack-build.sh && env'])
        for var in results.stdout.splitlines():
            if var.startswith(('STACK', 'ROCKS', 'PALLET', 'ROLL')):
                key, val = var.split('=')
                os.environ[key] = val


    def _interpolate_make_string(self, version):
        if '$(shell ' in version:
            match = re.search(r'(\$\(shell (.*)\))', version)
            if match:
                results = exec_cmd(match.groups()[1].split())
                version = version[:match.start(0)] + results.stdout.strip() + version[match.end(0):]
        return version


    def stamp_version(self):
        self.commit_id = git_get_current_commit_id()
        versionmk_loc = '{0}/{1}'.format(self.makefile_dir, 'version.mk')
        output_lines = []

        if self.branch != 'master':
            commit_label = '{0}_{1}'.format(self.branch, self.commit_id)
        else:
            commit_label = self.commit_id
        with open(versionmk_loc, 'r') as version_fh:
            for line in version_fh.readlines():
                if line.startswith(('VERSION', 'export ROLLVERSION', 'export VERSION', 'ROLLVERSION')):
                    lhs, version = line.split('=')
                    version = self._interpolate_make_string(version.strip())
                    self.src_version = version
                    line = '{0}= {1}_{2}\n'.format(lhs, version, commit_label)
                output_lines.append(line)

        with open(versionmk_loc, 'w') as version_fh:
            version_fh.writelines(output_lines)


    def do_build(self):
        log(self.global_build_log, 'starting build job for {0}'.format(self.pallet_name))
        self.refresh_git_repo()
        self.prepare_delivery_dir()
        self.prepare_build_dir()
        self.stamp_version()
        self.pre_make()
        self.make_pallet()
        self.deliver_iso()


    def do_meta_pallet_build(self):
        pass

if __name__ == '__main__':
    # grab build vars
    if len(sys.argv) != 2:
        log(GLOBAL_BUILD_LOG, 'you must specify a build.ini file')
        sys.exit(1)
    elif not os.path.isfile(sys.argv[1]):
        log(GLOBAL_BUILD_LOG, 'file {0} does not exist'.format(argv[1]))
        sys.exit(1)

    conf_file = sys.argv[1]

    build = Builder(conf_file)
    build.do_build()
