import logging
import platform
from django.conf import settings


class HostnameFilter(logging.Filter):
    """
    A logging filter to add the hostname to log records.
    """

    hostname = platform.node()

    def filter(self, record):
        if settings.SYSLOG_HOSTNAME:
            record.hostname = settings.SYSLOG_HOSTNAME
        else:
            record.hostname = HostnameFilter.hostname
        return True
