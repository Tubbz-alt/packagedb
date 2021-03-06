#!/usr/bin/python -tt
__requires__='TurboGears[future]'

import os
import glob
import re
from distutils.dep_util import newer
from distutils import log

from distutils.command.build_scripts import build_scripts as _build_scripts
from distutils.command.build import build as _build
from setuptools.command.install import install as _install
from setuptools.command.install_lib import install_lib as _install_lib

from setuptools import setup, find_packages
from turbogears.finddata import find_package_data

execfile(os.path.join("pkgdb", "release.py"))

class BuildScripts(_build_scripts, object):
    '''Build the package, changing the directories in start-pkgdb.'''
    substitutions = {'@CONFDIR@': '/usr/local/etc',
            '@DATADIR@': '/usr/local/share'}
    subRE = re.compile('('+'|'.join(substitutions.keys())+')+')
    # Set the correct directories in start-pkgdb
    user_options = _build_scripts.user_options
    user_options.extend([
    ('install-conf=', None, 'Installation directory for configuration files'),
    ('install-data=', None, 'Installation directory for data files')])

    def initialize_options(self):
        self.install_conf = None
        self.install_data = None
        super(BuildScripts, self).initialize_options()

    def finalize_options(self):
        self.set_undefined_options('build',
                ('install_conf', 'install_conf'),
                ('install_data', 'install_data'))
        self.substitutions['@CONFDIR@'] = self.install_conf or \
                '/usr/local/etc'
        self.substitutions['@DATADIR@'] = self.install_data or \
                '/usr/local/share'
        super(BuildScripts, self).finalize_options()

    def run(self):
        '''Substitute special variables with our install lcoations.

        '''
        for script in self.scripts:
            # If there's a script name with .in attached, make substitutions
            infile = script + '.in'
            if not os.path.exists(infile):
                continue
            if not self.force and not newer (infile, script):
                log.debug("not substituting in %s (up-to-date)", script)
                continue
            try:
                f = file(infile, 'r')
            except IOError:
                if not self.dry_run:
                    raise
                f = None
            outf = open(script, 'w')
            for line in f.readlines():
                matches = self.subRE.search(line)
                if matches:
                    for pattern in self.substitutions:
                        line = line.replace(pattern,
                                self.substitutions[pattern])
                outf.writelines(line)
            outf.close()
            f.close()
        super(BuildScripts, self).run()

class Build(_build, object):
    '''Override setuptools and install the package in the correct place for
    an application.'''

    user_options = _build.user_options
    user_options.extend([
    ('install-conf=', None, 'Installation directory for configuration files'),
    ('install-data=', None, 'Installation directory for data files')])

    def initialize_options(self):
        self.install_conf = None
        self.install_data = None
        super(Build, self).initialize_options()

    def finalize_options(self):
        self.install_conf = self.install_conf or '/usr/local/etc'
        self.install_data = self.install_data or '/usr/local/share'
        super(Build, self).finalize_options()

    def run(self):
        super(Build, self).run()

class Install(_install, object):
    '''Override setuptools and install the package in the correct place for
    an application.'''
    user_options = _install.user_options
    user_options.append( ('install-conf=', None,
            'Installation directory for configuration files'))
    user_options.append( ('install-data=', None,
            'Installation directory'))
    user_options.append( ('root=', None,
            'Install root'))

    def initialize_options(self):
        self.install_conf = None
        self.install_data = None
        self.root = None
        super(Install, self).initialize_options()

    def finalize_options(self):
        self.install_conf = self.install_conf or '/usr/local/etc'
        self.install_data = self.install_data or '/usr/local/share'
        super(Install, self).finalize_options()

class InstallApp(_install_lib, object):
    user_options = _install_lib.user_options
    user_options.append( ('install-conf=', None,
            'Installation directory for configuration files'))
    user_options.append( ('install-data=', None,
            'Installation directory'))
    user_options.append( ('root=', None,
            'Install root'))

    def initialize_options(self):
        self.install_conf = None
        self.install_data = None
        self.root = None
        super(InstallApp, self).initialize_options()

    def finalize_options(self):
        self.set_undefined_options('install',
                ('root', 'root'),
                ('install_conf', 'install_conf'),
                ('install_data', 'install_data'))
        print dir(self.distribution.get_name())
        self.install_dir=os.path.join(self.install_data, self.distribution.get_name())
        super(InstallApp, self).finalize_options()

    def run(self):
        super(InstallApp, self).run()

        ### FIXME: Couldn't think of a better way to do this in limited time

        # Install the configuration file to the confdir
        confdir = '%s%s%s' % (self.root, os.path.sep, self.install_conf)
        confdir.replace('//','/')
        self.mkpath(confdir)
        self.mkpath(os.path.join(confdir, 'fedmsg.d'))
        if not os.path.exists('pkgdb.cfg') \
                and os.path.exists('pkgdb.cfg.sample'):
            conf_src = 'pkgdb.cfg.sample'
        self.copy_file(conf_src, os.path.join(confdir, 'pkgdb.cfg'))
        self.copy_file('server-scripts/pkgdb-sync-bugzilla.cfg',
                os.path.join(confdir, 'pkgdb-sync-bugzilla.cfg'))
        self.copy_file('clients/pkgdb-client.cfg',
                os.path.join(confdir, 'pkgdb-client.cfg'))
        self.copy_file('fedmsg.d/pkgdb.py',
                os.path.join(confdir, 'fedmsg.d/pkgdb.py'))

setup(
    name=NAME,
    version=VERSION,

    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    download_url=DOWNLOAD_URL,
    license=LICENSE,

    cmdclass={'build_scripts': BuildScripts,
              'build': Build,
              'install': Install,
              'install_lib': InstallApp},
    install_requires = [
        "TurboGears[future] >= 1.0",
        "TurboMail",
        "python_fedora >= 0.3.12",
        "SQLAlchemy >= 0.5.5, < 0.7",
    ],
    scripts = ["start-pkgdb", "pkgdb.wsgi", "server-scripts/pkgdb-sync-yum",
        "server-scripts/pkgdb-sync-bugzilla", "clients/pkgdb-client",],
    # Note: these need to be installed somewhere in the data directory so that
    # the end user can upgrade the db "update-schema/pkgdb-0.3.10-0.3.11.py"
    # "update-schema/*"
    zip_safe=False,
    packages=find_packages(),
    package_data = find_package_data(where='pkgdb',
                                     package='pkgdb'),
    keywords = [
        # Use keywords if you'll be adding your package to the
        # Python Cheeseshop

        # if this has widgets, uncomment the next line
        # 'turbogears.widgets',

        # if this has a tg-admin command, uncomment the next line
        # 'turbogears.command',

        # if this has identity providers, uncomment the next line
        # 'turbogears.identity.provider',

        # If this is a template plugin, uncomment the next line
        # 'python.templating.engines',

        # If this is a full application, uncomment the next line
        'turbogears.app',
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: TurboGears',
        # if this is an application that you'll distribute through
        # the Cheeseshop, uncomment the next line
        'Framework :: TurboGears :: Applications',

        # if this is a package that includes widgets that you'll distribute
        # through the Cheeseshop, uncomment the next line
        # 'Framework :: TurboGears :: Widgets',
    ],
    test_suite='nose.collector',
    #entry_points = {
    #    'console_scripts': [
    #        'start-pkgdb = pkgdb.commands:start',
    #    ],
    #},
    )
