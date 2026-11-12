"""Single source of member write rules (SPEC V34).

`MembersPermissionHelper` (Wagtail modeladmin) and the `/api/app/members/`
write views both call this module, so the SPA can never become a second,
laxer door into the same writes.

The admin rules are deliberately odd — a superuser is denied add and edit
because it is treated as a platform operator, not a tenant — and mirroring
them is the point, not an accident. See SPEC §C.

Every `can_*` returns `(allowed, rule)`; `rule` is the machine-readable code
the 403 body carries (`{"error": ..., "rule": ...}`), `None` when allowed.
"""

from django.core.exceptions import ObjectDoesNotExist

from accounts.models import GroupOrganizations
from licenses.utils import is_license_valid

from .models import Members

SUPERUSER_NO_MEMBER_WRITE = "superuser_no_member_write"
QUOTA_EXCEEDED = "quota_exceeded"
GROUP_ORGANIZATION = "group_organization"
LICENSE_INVALID = "license_invalid"
NO_ORGANIZATION = "no_organization"
NO_FEATURES = "no_features"
PERM_MISSING = "perm_missing"


def _org_missing(user):
    """A user with no organization would crash the admin helper; deny instead."""
    return getattr(user, "organization", None) is None


def _quota_ok(user):
    """`Features.number_of_member` vs the org's member count.

    A missing Features row used to raise `AttributeError` inside the admin
    helper; here it denies instead, so an unconfigured org cannot write.
    """
    features = user.organization.features
    return features is not None and features.number_of_member >= _member_count(user)


def _member_count(user):
    return Members.objects.filter(organization=user.organization).count()


def _in_group_organization(user):
    try:
        GroupOrganizations.objects.get(main_org=user.organization)
        return True
    except ObjectDoesNotExist:
        return False


def can_add_member(user):
    if _org_missing(user):
        return False, NO_ORGANIZATION
    if not _quota_ok(user):
        return False, (
            NO_FEATURES if user.organization.features is None else QUOTA_EXCEEDED
        )
    if not user.has_perm("members.add_members"):
        return False, PERM_MISSING
    if user.is_superuser:
        return False, SUPERUSER_NO_MEMBER_WRITE
    if _in_group_organization(user):
        return False, GROUP_ORGANIZATION
    if not is_license_valid(user):
        return False, LICENSE_INVALID
    return True, None


def can_change_member(user, obj=None):
    if _org_missing(user):
        return False, NO_ORGANIZATION
    if not user.has_perm("members.change_members"):
        return False, PERM_MISSING
    if user.is_superuser:
        return False, SUPERUSER_NO_MEMBER_WRITE
    if _in_group_organization(user):
        return False, GROUP_ORGANIZATION
    if not is_license_valid(user):
        return False, LICENSE_INVALID
    return True, None


def can_delete_member(user, obj=None):
    # No superuser denial: the admin lets a superuser delete (SPEC §C).
    if _org_missing(user):
        return False, NO_ORGANIZATION
    if not user.has_perm("members.delete_members"):
        return False, PERM_MISSING
    if _in_group_organization(user):
        return False, GROUP_ORGANIZATION
    if not is_license_valid(user):
        return False, LICENSE_INVALID
    return True, None


def member_write_denial(user, obj, action):
    """`None` when allowed, else the rule code for `action` in {add,change,delete}."""
    if action == "add":
        allowed, rule = can_add_member(user)
    elif action == "change":
        allowed, rule = can_change_member(user, obj)
    elif action == "delete":
        allowed, rule = can_delete_member(user, obj)
    else:
        raise ValueError("unknown member write action: %r" % (action,))
    return None if allowed else rule
