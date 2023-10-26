import requests
#from datetime import datetime
from django.utils import timezone


class Headscale:
    def __init__(self, uri, token):
        self.uri = uri
        self.token = token
        self.header = {'Accept': 'application/json',
                       'Authorization': 'Bearer ' + self.token
                       }
        self.uri_prefix = '/api/v1'

    def query(self, methode, uri_command, data={}):
        try:
            if methode == 'GET':
                request = requests.get(uri_command, headers=self.header)
            elif methode == 'POST':
                request = requests.post(uri_command, headers=self.header, json=data)
            elif methode == 'DELETE':
                request = requests.delete(uri_command, headers=self.header)
            result = request.json()

        except requests.exceptions.RequestException:
            result = {'status': 0}

        return result

    def get_users(self):
        uri_command = self.uri + self.uri_prefix + '/user'
        return self.query('GET', uri_command)

    def add_user(self, username):
        uri_command = self.uri + self.uri_prefix + '/user'
        data = { 'name': username.lower() }
        return self.query('POST', uri_command, data)

    def delete_user(self, username):
        uri_command = self.uri + self.uri_prefix + '/user/' + username.lower()
        return self.query('DELETE', uri_command)

    def rename_user(self, current_user, new_user):
        uri_command = self.uri + self.uri_prefix + '/user/' + current_user.lower() + '/rename/' + new_user.lower()
        return self.query('POST', uri_command)

    def get_api_keys(self):
        uri_command = self.uri + self.uri_prefix + '/apikey'
        return self.query('GET', uri_command)

    def get_preauth_keys(self, username):
        uri_command = self.uri + self.uri_prefix + '/preauthkey?user=' + username.lower()
        return self.query('GET', uri_command)

    def add_preauth_key(self, username, reusable=False, ephemeral=False, expiration=None):
        uri_command = self.uri + self.uri_prefix + '/preauthkey'
        if expiration is None:
            expiration_time = timezone.now() + timezone.timedelta(hours=24)
            expiration = expiration_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
        data = {
                'user': username.lower(),
                'reusable': reusable,
                'ephemeral': ephemeral,
                'expiration': expiration
                }
        return self.query('POST', uri_command, data)

    def expire_preauth_key(self, username, key):
        uri_command = self.uri + self.uri_prefix + '/preauthkey/expire'
        data = {
                'user': username.lower(),
                'key': key
                }
        return self.query('POST', uri_command, data)

    def get_nodes(self):
        uri_command = self.uri + self.uri_prefix + '/node'
        return self.query('GET', uri_command)

    def get_node(self, nodeId):
        uri_command = self.uri + self.uri_prefix + '/node/' + nodeId
        return self.query('GET', uri_command)

    def delete_node(self, nodeId):
        uri_command = self.uri + self.uri_prefix + '/node/' + nodeId
        return self.query('DELETE', uri_command)

    def get_node_routes(self, nodeId):
        uri_command = self.uri + self.uri_prefix + '/node/' + nodeId + '/routes'
        return self.query('GET', uri_command)

    def rename_node(self, currentId, newId):
        uri_command = self.uri + self.uri_prefix + '/node/' + currentId + '/rename/' + newId
        return self.query('POST', uri_command)

    def move_node(self, nodeId, username):
        uri_command = self.uri + self.uri_prefix + '/node/' + nodeId + '/user?user=' + username
        return self.query('POST', uri_command)

