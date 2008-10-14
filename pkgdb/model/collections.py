# -*- coding: utf-8 -*-
#
# Copyright © 2007-2008  Red Hat, Inc. All rights reserved.
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
# Red Hat Author(s): Toshio Kuratomi <tkuratom@redhat.com>
#
'''
Mapping of collection related database tables to python classes
'''

from sqlalchemy import Table, Column, ForeignKey, Integer
from sqlalchemy import select, literal_column, not_
from sqlalchemy.orm import polymorphic_union, relation, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from turbogears.database import metadata, mapper, get_engine

from fedora.tg.json import SABase

from packages import PackageListing

get_engine()

#
# Mapped Tables
#

# Collections and Branches have an inheritance relationship.  ie: Branches are
# just Collections that have additional data.
CollectionTable = Table('collection', metadata, autoload=True)
BranchTable = Table('branch', metadata, autoload=True)

collectionJoin = polymorphic_union (
        {'b' : select((CollectionTable.join(
            BranchTable, CollectionTable.c.id == BranchTable.c.collectionid),
            literal_column("'b'").label('kind'))),
         'c' : select((CollectionTable, literal_column("'c'").label('kind')),
             not_(CollectionTable.c.id.in_(select(
                 (CollectionTable.c.id,),
                 CollectionTable.c.id == BranchTable.c.collectionid)
             )))
         },
        None
        )

#
# CollectionTable that shows number of packages in a collection
#
CollectionPackageTable = Table('collectionpackage', metadata,
        Column('id', Integer, primary_key=True),
        Column('statuscode', Integer,
            ForeignKey('collectionstatuscode.statuscodeid')),
        autoload=True)

#
# Mapped Classes
#

class Collection(SABase):
    '''A Collection of packages.

    Table -- Collection
    '''
    # pylint: disable-msg=R0902, R0903
    def __init__(self, name, version, statuscode, owner,
            publishurltemplate=None, pendingurltemplate=None, summary=None,
            description=None):
        # pylint: disable-msg=R0913
        super(Collection, self).__init__()
        self.name = name
        self.version = version
        self.statuscode = statuscode
        self.owner = owner
        self.publishurltemplate = publishurltemplate
        self.pendingurltemplate = pendingurltemplate
        self.summary = summary
        self.description = description

    def __repr__(self):
        return 'Collection(%r, %r, %r, %r, publishurltemplate=%r,' \
                ' pendingurltemplate=%r, summary=%r, description=%r)' % (
                self.name, self.version, self.statuscode, self.owner,
                self.publishurltemplate, self.pendingurltemplate,
                self.summary, self.description)

    def simple_name(self):
        '''Return a simple name for the Collection
        '''
        try:
            simple_name = self.branchname
        except AttributeError:
            simple_name = '-'.join((self.name, self.version))
        return simple_name

    @classmethod
    def by_simple_name(cls, simple_name):
        '''Return the Collection that matches the simple name

        :arg simple_name: simple name for a Collection
        :returns: The Collection that matches the name
        :raises sqlalchemy.InvalidRequestError: if the simple name is not found

        simple_name will be looked up first as the Branch name.  Then as the
        Collection name joined by a hyphen with the version.  ie:
        'Fedora EPEL-5'.
        '''
        try:
            collection = Branch.query.filter_by(branchname=simple_name).one()
        except InvalidRequestError:
            name, version = simple_name.rsplit('-')
            collection = Collection.query.filter_by(name=name,
                    version=version).one()
        return collection

class Branch(Collection):
    '''Collection that has a physical existence.

    Some Collections are only present as a name and collection of packages.  The
    Collections that have a branch record are also present in our VCS and
    download repositories.

    Table -- Branch
    '''
    # pylint: disable-msg=R0902, R0903
    def __init__(self, collectionid, branchname, disttag, parentid, *args):
        # pylint: disable-msg=R0913
        super(Branch, self).__init__(args)
        self.collectionid = collectionid
        self.branchname = branchname
        self.disttag = disttag
        self.parentid = parentid

    def __repr__(self):
        return 'Branch(%r, %r, %r, %r, %r, %r, %r, %r,' \
                ' publishurltemplate=%r, pendingurltemplate=%r,' \
                ' summary=%r, description=%r)' % (self.collectionid,
                self.branchname, self.disttag, self.parentid,
                self.name, self.version, self.statuscode, self.owner,
                self.publishurltemplate, self.pendingurltemplate,
                self.summary, self.description)

class CollectionPackage(SABase):
    '''Information about how many `Packages` are in a `Collection`

    View -- CollectionPackage
    '''
    # pylint: disable-msg=R0902, R0903
    def __repr__(self):
        # pylint: disable-msg=E1101
        return 'CollectionPackage(id=%r, name=%r, version=%r,' \
                ' statuscode=%r, numpkgs=%r,' % (
                self.id, self.name, self.version, self.statuscode,
                self.numpkgs)

#
# Mappers
#

collectionMapper = mapper(Collection, CollectionTable,
        select_table=collectionJoin, polymorphic_on=collectionJoin.c.kind,
        polymorphic_identity='c',
        properties = {
            # listings is deprecated.  It will go away in 0.4.x
            'listings': relation(PackageListing),
            # listings2 is slower than listings.  It has a front-end cost to
            # load the data into the dict.  However, if we're using listings
            # to search for multiple packages, this will likely be faster.
            # Have to look at how it's being used in production and decide
            # what to do.
            'listings2': relation(PackageListing, backref='collection',
                collection_class=attribute_mapped_collection('packagename')),
    })
mapper(Branch, BranchTable, inherits=collectionMapper,
        inherit_condition=CollectionTable.c.id==BranchTable.c.collectionid,
        polymorphic_identity='b')
mapper(CollectionPackage, CollectionPackageTable)
