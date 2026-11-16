import requests


def remove_duplicate_peers(peers):

    result = []
    ip_peer = []
    for peer in peers:
        if peer['address'] not in ip_peer:
            ip_peer.append(peer['address'])
            result.append(peer)

    return result


class Zerotier:
    def __init__(self, uri='http://localhost:9993', token='bde5492718141181c4059040'):
        self.uri = uri
        self.token = token
        self.header = {'X-ZT1-AUTH': self.token}
        #self.node_id = self.get_node_id()

    def get_node_id(self):
        status = self.status()
        return status['address']

    def query_ex(self, methode, uri_command, data={}):
        """`query()` plus the HTTP status: `(status_code|None, payload)`.

        `status_code is None` means the controller could not be asked at all,
        which is what callers must distinguish from "controller said 404"
        (SPEC V43). `payload` is None when the body was not JSON.
        """
        try:
            if methode == 'GET':
                request = requests.get(uri_command, headers=self.header)
            elif methode == 'POST':
                request = requests.post(uri_command, headers=self.header, json=data)
            elif methode == 'DELETE':
                request = requests.delete(uri_command, headers=self.header)
            return request.status_code, request.json()
        except (requests.exceptions.RequestException, ValueError):
            return None, None

    def query(self, methode, uri_command, data={}):
        # ponytail: JSON `null` bodies fold into {'status': 0} like failures.
        # ZeroTier never returns bare null; widen only if a real endpoint does.
        status, payload = self.query_ex(methode, uri_command, data)
        if status is None or payload is None:
            return {'status': 0}
        return payload

    def status(self):
        uri_command = self.uri + '/status'
        return self.query('GET', uri_command)

    def list_networks(self):
        #uri_command = self.uri + '/controller/network/'
        uri_command = self.uri + '/controller/network'
        result = self.query('GET', uri_command)
        return result

    @staticmethod
    def _member_url(network_id, member_id=None):
        url = '/controller/network/' + network_id + '/member'
        return url + '/' + member_id if member_id else url

    def list_members(self, network_id):
        return self.query('GET', self.uri + self._member_url(network_id))

    def list_members_ex(self, network_id):
        return self.query_ex('GET', self.uri + self._member_url(network_id))

    def get_network_info(self, network_id):
        #uri_command = self.uri + '/controller/network/' + network_id + '/'
        uri_command = self.uri + '/controller/network/' + network_id
        result = self.query('GET', uri_command)
        return result

    def get_member_info(self, network_id, member_id):
        return self.query('GET', self.uri + self._member_url(network_id, member_id))

    def get_member_info_ex(self, network_id, member_id):
        return self.query_ex('GET', self.uri + self._member_url(network_id, member_id))

    def add_network(self, network_id=None):
        if not network_id:
            uri_command = self.uri + '/controller/network/' + self.get_node_id() + '______'
        else:
            uri_command = self.uri + '/controller/network/' + network_id

        data = {}
        return self.query('POST', uri_command, data)

    def delete_network(self, network_id):
        uri_command = self.uri + '/controller/network/' + network_id
        return self.query('DELETE', uri_command)

    def add_member(self, network_id, member_id):
        pass

    def delete_member(self, network_id, member_id):
        return self.query('DELETE', self.uri + self._member_url(network_id, member_id))

    def set_network(self, network_id, data={}):
        #uri_command = self.uri + '/controller/network/' + network_id + '/'
        uri_command = self.uri + '/controller/network/' + network_id
        return self.query('POST', uri_command, data)

    def set_member(self, network_id, member_id, data={}):
        return self.query('POST', self.uri + self._member_url(network_id, member_id), data)

    def set_network_name(self, network_id, name):
        data = {'name': name}
        return self.set_network(network_id, data)

    def set_member_ipaddress(self, network_id, member_id, ipaddress=[]):
        data = {'ipAssignments': ipaddress}
        return self.set_member(network_id, member_id, data)

    def authorize_member(self, network_id, member_id, authorized=True):
        data = {'authorized': authorized}
        return self.set_member(network_id, member_id, data)

    def bridge_member(self, network_id, member_id, bridge=True):
        data = {'activeBridge': bridge}
        return self.set_member(network_id, member_id, data)

    def get_member_peers(self, member_id):
        uri_command = self.uri + '/peer/' + member_id
        peers = self.query('GET', uri_command)
        if 'paths' in peers and len(peers['paths']) != 0:
            clean_peers = remove_duplicate_peers(peers['paths'])
            peers['paths'] = clean_peers
        return peers
