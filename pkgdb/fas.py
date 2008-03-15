from fedora.tg.client import BaseClient, AuthError, ServerError
from turbogears import config

class AccountSystem(BaseClient):

    def __init__(self, baseURL, username=None, password=None, debug=False):
        super(AccountSystem, self).__init__(baseURL=baseURL, username=username, password=password, debug=debug)

    def group_by_id(self, id):
        """Returns a group object based on its id"""
        params = {'id': id}
        request = self.send_request('json/group_by_id', auth=True, input=params)
        if request['success']:
            return request['group']
        else:
            return dict()

    def person_by_id(self, id):
        """Returns a person object based on its id"""
        params = {'id': id}
        request = self.send_request('json/person_by_id', auth=True, input=params)
        if request['success']:
            return request['person']
        else:
            return dict()

    def group_by_name(self, groupname):
        """Returns a group object based on its name"""
        params = {'groupname': groupname}
        request = self.send_request('json/group_by_name', auth=True, input=params)
        if request['success']:
            return request['group']
        else:
            return dict()

    def person_by_username(self, username):
        """Returns a person object based on its username"""
        params = {'username': username}
        request = self.send_request('json/person_by_username', auth=True, input=params)
        if request['success']:
            return request['person']
        else:
            return dict()

    def user_id(self):
        """Returns a dict relating user IDs to usernames"""
        request = self.send_request('json/user_id', auth=True)
        return request['people']

