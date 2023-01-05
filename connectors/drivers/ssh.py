from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import SSHException, AuthenticationException
from django.conf import settings


def ssh(ipaddress, command, username=settings.SSH_DEFAULT_USER, password=settings.SSH_DEFAULT_PASS):
    """ SSH, run command and return result """
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        client.connect(ipaddress, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
    except SSHException or AuthenticationException:
        print('Error')
        return None

    output = stdout.read()
    client.close()

    return output.decode('utf-8')
