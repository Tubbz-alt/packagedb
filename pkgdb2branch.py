#!/usr/bin/python -tt
# Author: Toshio Kuratomi
# Copyright: 2007 Red Hat Software
# License: GPLv2 or later

import sys
try:
    import subprocess
except ImportError:
    import popen2

import json
import urllib2

try:
    from fedora.tg.client import BaseClient, ServerError
except ImportError:
    from client import BaseClient, ServerError

BASEURL='http://test3.fedora.phx.redhat.com/pkgdb-dev'
BRANCHER='/cvs/extras/CVSROOT/mkbranchwrapper'

class PackageDBError(ServerError):
    pass

class ProcessError(Exception):
    pass

class PackageDBClient(BaseClient):
    def __init__(self, baseURL):
        '''Initial ize the connection.

        Args:
        :baseURL: URL from which the packageDB is accessed
        '''
        # We're only performing read operations so we don't need a username
        super(PackageDBClient, self).__init__(baseURL, None, None)

    def get_package_branches(self, pkgname):
        data = self.send_request('/packages/name/%s' % pkgname)
        if 'message' in data:
            raise PackageDBError((data['message']))
        branches = []
        for packageListing in data['packageListings']:
            branches.append(packageListing['collection']['branchname'])
        return branches

def print_usage():
    print '''%s packagename [packagename, ...]

For each packagename specified as an argument, create any branches that are
listed for it in the packagedb.
''' % sys.argv[0]

def create_branches(pkgname, branches):
    cmdLine = [BRANCHER, pkgname]
    cmdLine.extend(branches)
    if 'subprocess' in sys.modules():
        branchScript = subprocess.Popen(cmdLine, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        retCode = branchScript.wait()
        if retCode:
            e = ProcessError()
            e.returnCode = retCode
            e.cmd = ' '.join(cmdLine)
            e.message = ''.join(branchScript.stdout.readlines())
            raise e
    else:
        branchScript = popen2.Popen4(' '.join(cmdLine))
        retCode = branchScript.wait()
        if os.WIFEXITED(retCode) and os.WEXITSTATUS(retCode):
            e = ProcessError()
            e.returnCode = os.WEXITSTATUS(retCode)
            e.cmd = ' '.join(cmdLine)
            e.message = ''.join(branchScript.fromchild.readlines())

if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv or len(sys.argv) == 1:
        print_usage()
        sys.exit(0)

    warnings = False
    packages = sys.argv[1:]
    client = PackageDBClient(BASEURL)
    for pkgname in packages:
        try:
            branches = client.get_package_branches(pkgname)
        except PackageDBError, e:
            print 'Unable to retrieve information about %s: %s' % (pkgname, e.message)
            warnings = True
            continue
        try:
            create_branches(pkgname, branches)
        except ProcessError, e:
            print 'Error, "%s" returned %s: %s' % (e.cmd, e.returncode,
                    e.message)
            warnings = True
            continue

    if warnings:
        sys.exit(100)
    sys.exit(0)
