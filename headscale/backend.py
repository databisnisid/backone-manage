import requests


class Headscale:
    def __init__(self, 
                 uri='https://hs.manage.backone.cloud', 
                 token='NuEuH1cnXQ.v_FpnNNEdA3IoldTQzDSvRTTKTEUw-KwlDFeCvkVbXo'):
        self.uri = uri
        self.token = token
        self.header = {'Accept': 'application/json',
                       'Authorization': 'Bearer ' + self.token
                       }

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
        uri_command = self.uri + '/api/v1/user'
        return self.query('GET', uri_command)

    def new_user(self, username):
        uri_command = self.uri + '/api/v1/user'
        data = { 'name': username.lower() }
        return self.query('POST', uri_command, data)

    def remove_user(self, username):
        uri_command = self.uri + '/api/v1/user/' + username.lower()
        return self.query('DELETE', uri_command)

    def rename_user(self, current_user, new_user):
        uri_command = self.uri + '/api/v1/user/' + current_user.lower() + '/rename/' + new_user.lower()
        return self.query('POST', uri_command)

    def get_api_keys(self):
        uri_command = self.uri + '/api/v1/apikey'
        return self.query('GET', uri_command)

    def get_preauth_keys(self, username):
        uri_command = self.uri + '/api/v1/preauthkey?user=' + username.lower()
        return self.query('GET', uri_command)

    def get_routes(self):
        uri_command = self.uri + '/api/v1/routes'
        return self.query('GET', uri_command)

    def get_devices(self):
        uri_command = self.uri + '/api/v1/machine'
        return self.query('GET', uri_command)

