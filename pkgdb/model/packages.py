# -*- coding: utf-8 -*-
#
# Copyright © 2007-2009  Red Hat, Inc.
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
# Fedora Project Author(s): Ionuț Arțăriși <mapleoin@fedoraproject.org>
#
'''
Mapping of package related database tables to python classes.

.. data:: DEFAULT_GROUPS
    Groups that get acls on the Package Database by default (in 0.3.x, the
    groups have to be listed here in order for them to show up in the Package
    Database at all.
'''
#
# PyLint Explanation
#

# :E1101: SQLAlchemy monkey patches the db fields into the class mappers so we
#   have to disable this check wherever we use the mapper classes.
# :W0201: some attributes are added to the model by SQLAlchemy so they don't
#   appear in __init__
# :R0913: The __init__ methods of the mapped classes may need many arguments
#   to fill the database tables.
# :C0103: Tables and mappers are constants but SQLAlchemy/TurboGears convention
#   is not to name them with all uppercase

from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.collections import mapped_collection, \
        attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.sql import and_

from turbogears.database import metadata, mapper, get_engine, session

from fedora.tg.json import SABase

from pkgdb.model.acls import PersonPackageListing, PersonPackageListingAcl, \
        GroupPackageListing, GroupPackageListingAcl
from pkgdb.model.prcof import RpmProvides, RpmConflicts, RpmRequires, \
        RpmObsoletes, RpmFiles

import logging
error_log = logging.getLogger('pkgdb.model.packages')

get_engine()

DEFAULT_GROUPS = {'provenpackager': {'commit': True, 'build': True,
    'checkout': True}}

#
# Tables
#

# Package and PackageListing are straightforward translations.  Look at these
# if you're looking for a straightforward example.

# :C0103: Tables and mappers are constants but SQLAlchemy/TurboGears convention
# is not to name them with all uppercase
#pylint:disable-msg=C0103
PackageTable = Table('package', metadata, autoload=True)
PackageListingTable = Table('packagelisting', metadata, autoload=True)

BinaryPackagesTable = Table('binarypackages', metadata, 
    Column('name', Text,  nullable=False, primary_key=True),
    useexisting=True
)

PackageBuildTable = Table('packagebuild', metadata, autoload=True)
PackageBuildDependsTable = Table('packagebuilddepends', metadata, autoload=True)

# association tables (many-to-many relationships)
PackageBuildListingTable = Table('packagebuildlisting', metadata,
        Column('packagelistingid', Integer, ForeignKey('packagelisting.id')),
        Column('packagebuildid', Integer, ForeignKey('packagebuild.id'))
)

#pylint:enable-msg=C0103
#
# Mapped Classes
#

class Package(SABase):
    '''Software we are packaging.

    This is equal to the software in one of our revision control directories.
    It is unversioned and not associated with a particular collection.

    Table -- Package
    '''
    def __init__(self, name, summary, statuscode, description=None,
            reviewurl=None, shouldopen=None, upstreamurl=None):
        #pylint:disable-msg=R0913
        super(Package, self).__init__()
        self.name = name
        self.summary = summary
        self.statuscode = statuscode
        self.description = description
        self.reviewurl = reviewurl
        self.shouldopen = shouldopen
        self.upstreamurl = upstreamurl

    def __repr__(self):
        return 'Package(%r, %r, %r, description=%r, ' \
               'upstreamurl=%r, reviewurl=%r, shouldopen=%r)' % (
                self.name, self.summary, self.statuscode, self.description,
                self.upstreamurl, self.reviewurl, self.shouldopen)

    def create_listing(self, collection, owner, status,
            qacontact=None, author_name=None):
        '''Create a new PackageListing branch on this Package.

        :arg collection: Collection that the new PackageListing lives on
        :arg owner: The owner of the PackageListing
        :arg status: Status to set the PackageListing to
        :kwarg qacontact: QAContact for this PackageListing in bugzilla.
        :kwarg author_name: Author of the change.  Note: will remove when
            logging is made generic
        :returns: The new PackageListing object.

        This creates a new PackageListing for this Package.  The PackageListing
        has default values set for group acls.
        '''
        from pkgdb.utils import STATUS
        from pkgdb.model.logs import PackageListingLog
        pkg_listing = PackageListing(owner, status.statuscodeid,
                collectionid=collection.id,
                qacontact=qacontact)
        pkg_listing.package = self
        for group in DEFAULT_GROUPS:
            new_group = GroupPackageListing(group)
            #pylint:disable-msg=E1101
            pkg_listing.groups2[group] = new_group
            #pylint:enable-msg=E1101
            for acl, status in DEFAULT_GROUPS[group].iteritems():
                if status:
                    acl_status = STATUS['Approved'].statuscodeid
                else:
                    acl_status = STATUS['Denied'].statuscodeid
                group_acl = GroupPackageListingAcl(acl, acl_status)
                # :W0201: grouppackagelisting is added to the model by
                #   SQLAlchemy so it doesn't appear in __init__
                #pylint:disable-msg=W0201
                group_acl.grouppackagelisting = new_group
                #pylint:enable-msg=W0201

        # Create a log message
        log = PackageListingLog(author_name,
                STATUS['Added'].statuscodeid,
                '%(user)s added a %(branch)s to %(pkg)s' %
                {'user': author_name, 'branch': collection,
                    'pkg': self.name})
        log.listing = pkg_listing

        return pkg_listing


class BinaryPackage(SABase):

    def __init__(self, name):
        super(BinaryPackage, self).__init__()
        self.name = name


    def __repr__(self):
        return 'BinaryPackage(%r)' % self.name



class PackageListing(SABase):
    '''This associates a package with a particular collection.

    Table -- PackageListing
    '''
    def __init__(self, owner, statuscode, packageid=None, collectionid=None,
            qacontact=None, specfile=None):
        #pylint:disable-msg=R0913
        super(PackageListing, self).__init__()
        self.packageid = packageid
        self.collectionid = collectionid
        self.owner = owner
        self.qacontact = qacontact
        self.statuscode = statuscode
        self.specfile = specfile

    packagename = association_proxy('package', 'name')

    def __repr__(self):
        return 'PackageListing(%r, %r, packageid=%r, collectionid=%r,' \
               ' qacontact=%r, specfile=%r)' % (self.owner, self.statuscode,
                        self.packageid, self.collectionid, self.qacontact,
                        self.specfile)

    def clone(self, branch, author_name):
        '''Clone the permissions on this PackageListing to another `Branch`.

        :arg branch: `branchname` to make a new clone for
        :arg author_name: Author of the change.  Note, will remove when logs
            are made generic
        :raises sqlalchemy.exceptions.InvalidRequestError: when a request
            does something that violates the SQL integrity of the database
            somehow.
        :returns: new branch
        :rtype: PackageListing
        '''
        from pkgdb.utils import STATUS
        from pkgdb.model.collections import Branch
        from pkgdb.model.logs import GroupPackageListingAclLog, \
                PersonPackageListingAclLog
        # Retrieve the PackageListing for the to clone branch
        try:
            #pylint:disable-msg=E1101
            clone_branch = PackageListing.query.join('package'
                    ).join('collection').filter(
                        and_(Package.name==self.package.name,
                            Branch.branchname==branch)).one()
            #pylint:enable-msg=E1101
        except InvalidRequestError:
            ### Create a new package listing for this release ###

            # Retrieve the collection to make the branch for
            #pylint:disable-msg=E1101
            clone_collection = Branch.query.filter_by(branchname=branch).one()
            #pylint:enable-msg=E1101
            # Create the new PackageListing
            clone_branch = self.package.create_listing(clone_collection,
                    self.owner, STATUS['Approved'], qacontact=self.qacontact,
                    author_name=author_name)

        log_params = {'user': author_name,
                'pkg': self.package.name, 'branch': branch}
        # Iterate through the acls in the master_branch
        #pylint:disable-msg=E1101
        for group_name, group in self.groups2.iteritems():
        #pylint:enable-msg=E1101
            log_params['group'] = group_name
            if group_name not in clone_branch.groups2:
                # Associate the group with the packagelisting
                #pylint:disable-msg=E1101
                clone_branch.groups2[group_name] = \
                        GroupPackageListing(group_name)
                #pylint:enable-msg=E1101
            clone_group = clone_branch.groups2[group_name]
            for acl_name, acl in group.acls2.iteritems():
                if acl_name not in clone_group.acls2:
                    clone_group.acls2[acl_name] = \
                            GroupPackageListingAcl(acl_name, acl.statuscode)
                else:
                    # Set the acl to have the correct status
                    if acl.statuscode != clone_group.acls2[acl_name].statuscode:
                        clone_group.acls2[acl_name].statuscode = acl.statuscode

                # Create a log message for this acl
                log_params['acl'] = acl.acl
                log_params['status'] = acl.status.locale['C'].statusname
                log_msg = '%(user)s set %(acl)s status for %(group)s to' \
                        ' %(status)s on (%(pkg)s %(branch)s)' % log_params
                log = GroupPackageListingAclLog(author_name,
                        acl.statuscode, log_msg)
                log.acl = clone_group.acls2[acl_name]

        #pylint:disable-msg=E1101
        for person_name, person in self.people2.iteritems():
        #pylint:enable-msg=E1101
            log_params['person'] = person_name
            if person_name not in clone_branch.people2:
                # Associate the person with the packagelisting
                #pylint:disable-msg=E1101
                clone_branch.people2[person_name] = \
                        PersonPackageListing(person_name)
                #pylint:enable-msg=E1101
            clone_person = clone_branch.people2[person_name]
            for acl_name, acl in person.acls2.iteritems():
                if acl_name not in clone_person.acls2:
                    clone_person.acls2[acl_name] = \
                            PersonPackageListingAcl(acl_name, acl.statuscode)
                else:
                    # Set the acl to have the correct status
                    if clone_person.acls2[acl_name].statuscode \
                            != acl.statuscode:
                        clone_person.acls2[acl_name].statuscode = acl.statuscode
                # Create a log message for this acl
                log_params['acl'] = acl.acl
                log_params['status'] = acl.status.locale['C'].statusname
                log_msg = '%(user)s set %(acl)s status for %(person)s to' \
                        ' %(status)s on (%(pkg)s %(branch)s)' % log_params
                log = PersonPackageListingAclLog(author_name,
                        acl.statuscode, log_msg)
                log.acl = clone_person.acls2[acl_name]

        return clone_branch

def collection_alias(pkg_listing):
    '''Return the collection_alias that a package listing belongs to.

    :arg pkg_listing: PackageListing to find the Collection for.
    :returns: Collection Alias.  This is either the branchname or a combination
        of the collection name and version.

    This is used to make Branch keys for the dictionary mapping of pkg listings
    into packages.
    '''
    return pkg_listing.collection.simple_name

class PackageBuildDepends(SABase):
    '''PackageBuild Dependencies to one another.

    Table(junction) -- PackageBuildDepends
    '''
    def __init__(self, packagebuildname, packagebuildid=None):
        super(PackageBuildDepends, self).__init__()
        self.packagebuildid = packagebuildid
        self.packagebuildname = packagebuildname

    def __repr__(self):
        return 'PackageBuildDepends(%r, %r)' % (
            self.packagebuildid, self.packagebuildname)



class PackageBuild(SABase):
    '''Package Builds - Actual rpms

    This is a very specific unitary package with version, release and everything.

    Table -- PackageBuild
    '''
    def __init__(self, name, packageid, epoch, version, release, architecture,
                 size, license, changelog, committime, committer,
                 repoid):
        super(PackageBuild, self).__init__()
        self.name = name
        self.packageid = packageid
        self.epoch = epoch
        self.version = version
        self.release = release
        self.architecture = architecture
        self.size = size
        self.license = license
        self.changelog = changelog
        self.committime = committime
        self.committer = committer
        self.repoid = repoid

    def __repr__(self):
        return 'PackageBuild(%r, packageid=%r, epoch=%r, version=%r,' \
               ' release=%r, architecture=%r, size=%r, license=%r,' \
               ' changelog=%r, committime=%r, committer=%r, repoid=%r)' % (
            self.name, self.packageid, self.epoch, self.version,
            self.release, self.architecture, self.size,
            self.license, self.changelog, self.committime, self.committer,
            self.repoid)

    def __str__(self):
        return "%s-%s%s-%s.%s" % (self.name,
                ('', self.epoch+':')[bool(int(self.epoch))], self.version, 
                self.release, self.architecture)

    def download_path(self):
        return "%s%s%s%s.rpm" % (self.repo.mirror, self.repo.url, 
                ('','Packages/')[self.repo.url.endswith('os/')], self)
    
    def scores(self):
        '''Return a dictionary of tagname: score for a given packegebuild
        '''

        scores = {}
        for app in self.applications: #pylint:disable-msg=E1101
            tags = app.scores
            for tag, score in tags.iteritems():
                sc = scores.get(tag, None)
                if sc is None or sc < score:
                    scores[tag] = score

        return scores


    @classmethod
    def most_fresh(self, limit=5):
        """Query that returns last pkgbuild imports

        :arg limit: top <limit> apps

        Excerpt from changelog is returned as well
        """
        #pylint:disable-msg=E1101
        fresh = session.query(PackageBuild)\
                .order_by(PackageBuild.committime.desc())
        #pylint:enable-msg=E1101
        if limit > 0:
            fresh = fresh.limit(limit)
        return fresh

#
# Mappers
#

mapper(Package, PackageTable, properties={
    # listings is here for compatibility.  Will be removed in 0.4.x
    'listings': relation(PackageListing),
    'listings2': relation(PackageListing,
        backref=backref('package'),
        collection_class=mapped_collection(collection_alias)),
    'builds': relation(PackageBuild,
        backref=backref('package'),
        collection_class=attribute_mapped_collection('name'))
    })

mapper(PackageListing, PackageListingTable, properties={
    'people': relation(PersonPackageListing),
    'people2': relation(PersonPackageListing, backref=backref('packagelisting'),
        collection_class = attribute_mapped_collection('username')),
    'groups': relation(GroupPackageListing),
    'groups2': relation(GroupPackageListing, backref=backref('packagelisting'),
        collection_class = attribute_mapped_collection('groupname')),
    })

mapper(PackageBuildDepends, PackageBuildDependsTable)

mapper(PackageBuild, PackageBuildTable, properties={
    'conflicts': relation(RpmConflicts, backref=backref('build'),
        collection_class = attribute_mapped_collection('name'),
        cascade='all, delete-orphan'),
    'requires': relation(RpmRequires, backref=backref('build'),
        collection_class = attribute_mapped_collection('name'),
        cascade='all, delete-orphan'),
    'provides': relation(RpmProvides, backref=backref('build'),
        collection_class = attribute_mapped_collection('name'),
        cascade='all, delete-orphan'),
    'obsoletes': relation(RpmObsoletes, backref=backref('build'),
        collection_class = attribute_mapped_collection('name'),
        cascade='all, delete-orphan'),
    'files': relation(RpmFiles, backref=backref('build'),
        collection_class = attribute_mapped_collection('name'),
        cascade='all, delete-orphan'),
    'depends': relation(PackageBuildDepends, backref=backref('build'),
        collection_class = attribute_mapped_collection('packagebuildname'),
        cascade='all, delete-orphan'),
    'listings': relation(PackageListing, backref=backref('builds'),
        secondary = PackageBuildListingTable),
    })


mapper(BinaryPackage, BinaryPackagesTable,
    properties={
        'packagebuilds': relation(PackageBuild, cascade='all'),
    })


