# -*- coding: utf-8 -*-
#
# Copyright © 2009 Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Fedora Project Author(s): Ionuț Arțăriși <mapleoin@fedoraproject.org>
#
'''
Mapping of language related database tables to python classes.
'''

from sqlalchemy import Table
from sqlalchemy.orm import relation, backref
from sqlalchemy.sql import or_

from turbogears.database import metadata, mapper, session

from fedora.tg.json import SABase

#
# Tables
#

LanguagesTable = Table('languages', metadata, autoload=True)

#
# Mapped Classes
#

class Language(SABase):
    '''Language.

    A list of languages that currently have localizations in fedora and will
    hopefully have localizations in pkgdb.

    Table -- Languages
    '''

    def __init__(self, name, shortname):
        super(Language, self).__init__()
        self.name = name
        self.shortname = shortname

    def __repr__(self):
        return 'Language(%r, %r)' % (self.name, self.shortname)

    @classmethod
    def find(self, language):
        '''Returns a shortname after searching for both short and longname.

        :arg name: a short or long Language name
        '''

        return session.query(Language).filter(or_(Language.name==language,
                                         Language.shortname==language
                                         )).one()
#
# Mappers
#

mapper(Language, LanguagesTable)
