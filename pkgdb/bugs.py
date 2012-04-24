# -*- coding: utf-8 -*-
#
# Copyright © 2007-2010  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2, or (at your option) any later version.  This
# program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the GNU
# General Public License along with this program; if not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA. Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public License and
# may only be used or replicated with the express permission of Red Hat, Inc.
#
# Red Hat Author(s):        Toshio Kuratomi <tkuratom@redhat.com>
#                           Seth Vidal <svidal@redhat.com>
# Fedora Project Author(s): Ionuț Arțăriși <mapleoin@fedoraproject.org>
#
'''
Controller for displaying Package Bug Information.
'''
#
# PyLint Explanations
#

# :E1101: SQLAlchemy mapped classes are monkey patched.  Unless otherwise
#   noted, E1101 is disabled due to a static checker not having information
#   about the monkey patches.

from urllib import quote
import xmlrpclib
from turbogears import controllers, expose, config, redirect
try:
    from sqlalchemy.exceptions import InvalidRequestError
except ImportError:
    from sqlalchemy.exc import InvalidRequestError

from cherrypy import request
from fedora.tg.tg1utils import request_format
from operator import itemgetter, attrgetter


try:
    # python-bugzilla 0.4 >= rc5
    from bugzilla.base import _Bug as Bug
except ImportError:
    try:
        # python-bugzilla 0.4 < rc5
        from bugzilla.base import Bug
    except ImportError:
        # python-bugzilla 0.3
        # :E0611: This is only found if we are using python-bugzilla 0.3
        from bugzilla import Bug # pylint: disable-msg=E0611

try:
    from fedora.textutils import to_unicode
except ImportError:
    from pkgdb.lib.utils import to_unicode

from pkgdb.model import Package
from pkgdb.letter_paginator import Letters
from pkgdb.lib.utils import LOG, get_bz
from pkgdb import _

from bugzilla import base
def getbugssimple(self,idlist):
    '''Return a list of Bug objects for the given bug ids, populated with
    simple info. As with getbugs(), if there's a problem getting the data
    for a given bug ID, the corresponding item in the returned list will
    be None.'''
    mc = self._multicall()
    for id in idlist:
        mc._getbugsimple(id)
    raw_results = mc.run()
    del mc
    return [Bug(self,dict=b) for b in raw_results]
base.BugzillaBase.getbugssimple = getbugssimple

class BugList(list):
    '''Transform and store values in the bugzilla.Bug data structure

    The bugzilla.Bug data structure uses 8-bit strings instead of unicode and
    will have a private url instead of a public one.  Storing the bugs in this
    list object will cause these values to be corrected.
    '''

    def __init__(self, query_url, public_url):
        super(BugList, self).__init__()
        self.query_url = query_url
        self.public_url = public_url

    def __convert(self, bug):
        '''Convert bugs from the raw form retrieved from python-bugzilla to
        one that is consumable by a normal python program.

        This involves converting byte strings to unicode type and substituting
        any private URLs returned into a public URL.  (This occurs when we
        have to call bugzilla via one name on the internal network but someone
        clicking on the link in a web page needs to use a different address.)

        :arg bug: A bug record returned from the python-bugzilla interface.
        '''
        if not isinstance(bug, Bug):
            raise TypeError(_('Can only store bugzilla.Bug type'))
        if self.query_url != self.public_url:
            bug.url = bug.url.replace(self.query_url, self.public_url)

        bug.bug_status = to_unicode(bug.bug_status)
        bug.short_desc = to_unicode(bug.short_desc)
        bug.product = to_unicode(bug.product)
        return {'url': bug.url, 'bug_status': bug.bug_status,
                'short_desc': bug.short_desc, 'bug_id': bug.bug_id,
                'product': bug.product, 'version': 'Unknown', 'keywords': ''}

    def __setitem__(self, index, bug):
        bug = self.__convert(bug)
        super(BugList, self).__setitem__(index, bug)

    def append(self, bug):
        '''Override the default append() to convert URLs and unicode.

        Just like __setitem__(), we need to call our __convert() method when
        adding a new bug via append().  This makes sure that we convert urls
        to the public address and convert byte strings to unicode.
        '''
        bug = self.__convert(bug)
        super(BugList, self).append(bug)

class Bugs(controllers.Controller):
    '''Display information related to individual packages.
    '''
    bzUrl = config.get('bugzilla.url',
                'https://bugzilla.redhat.com/')
    bzQueryUrl = config.get('bugzilla.queryurl', bzUrl)

    def __init__(self, app_title=None):
        '''Create a Packages Controller.

        :app_title: Title of the web app.
        '''

        self.app_title = app_title
        self.list = Letters(app_title)

    @expose(template='pkgdb.templates.pkgbugs', allow_json=True)
    def default(self, package_name, *args, **kwargs):
        '''Display a list of Fedora bugs against a given package.'''
        # Nasty, nasty hack.  The packagedb, via bugz.fp.o is getting sent
        # requests to download files.  These refused to go away even when
        # we fixed up the apache redirects.  Send them to download.fp.o
        # manually.

        def bug_sort(arg1, arg2):
            if (arg1['product'] < arg2['product']):
                return -1

            elif (arg1['product'] > arg2['product']):
                return 1

            else:
                #
                # version is a string which may contain an integer such as 13 or
                # a string such as 'rawhide'.  We want the integers first in
                # decending order followed by the strings.
                #
                try:
                    val1 = int(arg1['version'])
                    try:
                        val2 = int(arg2['version'])
                    except ValueError:
                        return -1
                except ValueError:
                    try:
                        val2 = int(arg2['version'])
                        return 1
                    except ValueError:
                        val1 = arg1['version']
                        val2 = arg2['version']

                if (val1 < val2):
                    return 1

                elif (val1 > val2):
                    return -1

                else:
                    if (arg1['bug_id'] < arg2['bug_id']):
                        return -1

                    elif (arg1['bug_id'] < arg2['bug_id']):
                        return -1

                    return 0

        if args or kwargs:
            if args:
                url = 'http://download.fedoraproject.org/' \
                        + quote(package_name) \
                        + '/' + '/'.join([quote(a) for a in args])
            elif kwargs:
                url = 'http://mirrors.fedoraproject.org/' \
                        + quote(package_name) \
                        + '?' + '&'.join([quote(q) + '=' + quote(v) for (q, v)
                            in kwargs.items()])
                LOG.warning(_('Invalid URL: redirecting: %(url)s') %
                        {'url':url})
            raise redirect(url)

        query = {'product': ('Fedora', 'Fedora EPEL'),
                'component': package_name,
                'bug_status': ('ASSIGNED', 'NEW', 'MODIFIED',
                    'ON_DEV', 'ON_QA', 'VERIFIED', 'FAILS_QA',
                    'RELEASE_PENDING', 'POST') }
        
        # :E1101: python-bugzilla monkey patches this in
        try:
            bugzilla = get_bz()
        except xmlrpclib.ProtocolError:
            error = dict(status=False,
                    title=_('%(app)s -- Unable to contact bugzilla') %
                        {'app': self.app_title},
                    message=_('Bugzilla is unavailable.  Unable to determine'
                        ' bugs for %(pkg)s') % {'pkg': package_name})
            if request_format() != 'json':
                error['tg_template'] = 'pkgdb.templates.errors'
            return error

        raw_bugs = bugzilla.query(query) # pylint: disable-msg=E1101
        bugs = BugList(self.bzQueryUrl, self.bzUrl)
        bug_ids = []
        for bug in raw_bugs:
            bugs.append(bug)
            bug_id = bugs[-1]['bug_id']
            bug_ids.append(bug_id)

        bug_details = bugzilla.getbugssimple(bug_ids)

        if bugs:
            for bug in bugs:
                bug_id1 = bug['bug_id']
                for i in range(len(bug_details)):
                    bug_info = bug_details[i]
                    if bug_id1 == bug_info.bug_id:
                        bug['version'] = bug_info.version
                        if ('Triaged' in bug_info.keywords):
                            bug['keywords'] = 'Triaged'
                        del bug_details[i]
                        break

        if not bugs:
            # Check that the package exists
            try:
                # pylint: disable-msg=E1101
                Package.query.filter_by(name=package_name).one()
            except InvalidRequestError:
                error = dict(status=False,
                        title=_('%(app)s -- Not a Valid Package Name') %
                            {'app': self.app_title},
                        message=_('No such package %(pkg)s') %
                            {'pkg': package_name})
                if request_format() != 'json':
                    error['tg_template'] = 'pkgdb.templates.errors'
                return error

        bugs.sort(cmp=bug_sort)
        return  dict(title=_('%(app)s -- Open Bugs for %(pkg)s') %
                {'app': self.app_title, 'pkg': package_name},
                package=package_name, bugs=bugs)
