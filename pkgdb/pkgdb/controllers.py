import sqlalchemy
from turbogears import controllers, expose
from pkgdb import model
from turbogears import identity, redirect
from cherrypy import request, response
from pkgdb import json
# import logging
# log = logging.getLogger("pkgdb.controllers")

# The Fedora Account System Module
import website

appTitle = 'Fedora Package Database'

class Test(controllers.RootController):
    @expose(template="pkgdb.templates.welcome")
    @identity.require(identity.in_group("first1"))
    def index(self):
        import time
        # log.debug("Happy TurboGears Controller Responding For Duty")
        return dict(now=time.ctime())

    @expose(template="pkgdb.templates.try")
    def test(self):
        return dict(title='Test Page', rows=({'1': 'alligator', '2':'bat'},{'1':'avocado', '2':'bannana'}))

class Collections(controllers.Controller):
    @expose(template='pkgdb.templates.collectionoverview')
    def index(self):
        '''List the Collections we know about.
        '''
        collectionPkg = sqlalchemy.select(
                (model.PackageListingTable.c.collectionid.label('id'),
                    sqlalchemy.func.count(1).label('numpkgs')),
                group_by=(model.PackageListingTable.c.collectionid,)).alias(
                        'collectionpkg')
        collections = sqlalchemy.select(
                (model.CollectionTable, collectionPkg.c.numpkgs),
                model.CollectionTable.c.id == collectionPkg.c.id,
                order_by=(model.CollectionTable.c.name,
                    model.CollectionTable.c.version)).execute()

        return dict(title=appTitle + ' -- Collection Overview',
                collections=collections)

    @expose(template='pkgdb.templates.collectionpage')
    def id(self, collectionId):
        '''Return a page with information on a particular Collection
        '''
        try:
            collectionId = int(collectionId)
        except ValueError:
            raise redirect('/collections/not_id')
        ### FIXME: Want to return additional info:
        # date it was created (join log table: creation date)
        collection = sqlalchemy.select((model.CollectionTable.c.name,
            model.CollectionTable.c.version, model.CollectionTable.c.owner,
            model.CollectionTable.c.summary, model.CollectionTable.c.description,
            model.StatusTranslationTable.c.statusname),
            sqlalchemy.and_(
                model.CollectionTable.c.status==model.StatusTranslationTable.c.statuscodeid,
                model.StatusTranslationTable.c.language=='C',
                model.CollectionTable.c.id==collectionId), limit=1).execute()
        if collection.rowcount <= 0:
            raise redirect('/collections/unknown',
                    redirect_params={'collectionId':collectionId})
        collection = collection.fetchone()
        ### FIXME: Have to extract better ownership information from the
        # Fedora accounts system
        collection.owner = website.get_user_info(website.get_dbh(), collection.owner)['realname']

        # Retrieve the packagelist for this collection
        packages = sqlalchemy.select((model.PackageTable.c.name,
            model.PackageListingTable.c.packageid),
            sqlalchemy.and_(
                model.PackageListingTable.c.collectionid == collectionId,
                model.PackageListingTable.c.packageid==model.PackageTable.c.id),
            order_by=(model.PackageTable.c.name,)).execute()
        if packages.rowcount <= 0:
            packages = tuple()
        else:
            packages = packages.fetchall()
        return dict(title='%s -- %s %s' % (appTitle, collection.name,
            collection.version), collection=collection, packages=packages)

    @expose(template='pkgdb.templates.errors')
    def unknown(self, collectionId):
        msg = 'The collectionId you were linked to, %s, does not exist.' \
                ' If you received this error from a link on the' \
                ' fedoraproject.org website, please report it.' % collectionId
        return dict(title=appTitle + ' -- Unknown Collection', msg=msg)

    @expose(template='pkgdb.templates.errors')
    def not_id(self):
        msg = 'The collectionId you were linked to is not a valid id.' \
                ' If you received this error from a link on the' \
                ' fedoraproject.org website, please report it.'
        return dict(title=appTitle + ' -- Invalid Collection Id', msg=msg)

class Packages(controllers.RootController):
    @expose(template='pkgdb.templates.pkgoverview')
    def index(self):
        return dict(title=appTitle + ' -- Package Overview')

    @expose(template='pkgdb.templates.pkgpage')
    def id(self, packageId):
        return dict(title=appTitle)

class Root(controllers.RootController):
    test = Test()
    collections = Collections()
    packages = Packages()

    @expose(template='pkgdb.templates.overview')
    def index(self):
        return dict(title=appTitle)

    @expose(template="pkgdb.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):
        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            raise redirect(forward_url)

        forward_url=None
        previous_url= request.path

        if identity.was_login_attempted():
            msg=_("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg=_("You must provide your credentials before accessing "
                   "this resource.")
        else:
            msg=_("Please log in.")
            forward_url= request.headers.get("Referer", "/")
            
        response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url)

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect("/")

