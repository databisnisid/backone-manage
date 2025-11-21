import logging
import platform
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)


class HostnameFilter(logging.Filter):
    """
    A logging filter to add the hostname to log records.
    """

    hostname = platform.node()

    def filter(self, record):
        if (
            settings.SYSLOG_HOSTNAME
            and settings.SYSLOG_HOSTNAME != "manage.backone.cloud"
        ):
            record.hostname = settings.SYSLOG_HOSTNAME
        else:
            record.hostname = HostnameFilter.hostname
        return True


# Get an instance of a logger
logger = logging.getLogger("auth_event")


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    """
    Receiver to log user login events.
    """
    if request:
        # Get the IP address (basic implementation, might need refinement for production behind proxies)
        # ip_address = request.META.get("REMOTE_ADDR", "")
        ip_address = request.META.get("X_FORWARDED_FOR", "")
        log_message = f'User logged in: username="{user.get_username()}", ip_address="{ip_address}"'
        logger.info(log_message)
    else:
        # Handle cases where the request object might not be available (e.g., management commands)
        log_message = (
            f'User logged in: username="{user.get_username()}" (no request object)'
        )
        logger.info(log_message)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        logger.info(f"User logged out: {user.username} (ID: {user.id})")
    else:
        logger.info("A user was logged out (username not available).")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Log failed login attempts to the configured syslog handler.
    """
    # Extract useful information like username and IP address
    username = credentials.get("username", "")
    # ip_address = request.META.get("REMOTE_ADDR", "Unknown IP")
    ip_address = request.META.get("X_FORWARDED_FOR", "Unknown IP")

    # Log the error message using the custom logger
    logger.error(
        f'FAILED LOGIN attempt for username: "{username}" from IP: {ip_address}'
    )
