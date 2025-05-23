# from enum import unique
from django.db import models

# from django.template.defaultfilters import default
from django.utils.translation import gettext as _
from django.contrib.auth.models import AbstractUser
from controllers.models import Controllers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import uuid
from wagtail.models import Site
from wagtail.images import get_image_model_string
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey, ParentalManyToManyField


class Features(models.Model):
    name = models.CharField(_("Name"), max_length=50, unique=True)
    description = models.TextField(_("Description"))

    # Network
    number_of_network = models.IntegerField(_("Number of Networks"), default=1)
    network_multi_ip = models.BooleanField(_("Network Multi IP"), default=False)
    network_rules = models.BooleanField(_("Network Rules"), default=False)
    # Member
    number_of_member = models.IntegerField(_("Number of Members"), default=10)
    member_multi_ip = models.BooleanField(_("Member Multi IP"), default=False)
    authorize = models.BooleanField(_("Authorize"), default=False)
    bridge = models.BooleanField(_("Bridge"), default=False)
    tags = models.BooleanField(_("Tags"), default=False)
    web = models.BooleanField(_("Remote Web"), default=False)
    ssh = models.BooleanField(_("Remote SSH"), default=False)
    synchronize = models.BooleanField(_("Synchronize"), default=False)

    geolocation = models.BooleanField(_("GeoLocation"), default=False)
    online_offline = models.BooleanField(_("Online/Offline"), default=False)
    is_export = models.BooleanField(_("Export Data"), default=False)
    mobile_connect = models.BooleanField(_("Mobile Connect"), default=False)
    map_dashboard = models.BooleanField(_("Map Dashboard"), default=False)
    is_nms = models.BooleanField(_("Monitoring"), default=False)

    # WebFilters
    is_webfilter = models.BooleanField(_("Web Filters"), default=False)
    is_webfilter_multinet = models.BooleanField(
        _("Web Filters Multi Net"), default=False
    )

    # DPI Netify
    is_dpi = models.BooleanField(_("DPI"), default=False)

    # Project Related
    is_telkomsel = models.BooleanField(_("Telkomsel Project"), default=False)

    # Custom List
    is_simple_list = models.BooleanField(_("Simple List"), default=False)
    is_lte_signal = models.BooleanField(_("LTE Signal"), default=False)

    # uuid = models.UUIDField(_('UUID'), blank=True, null=True)
    # uuid = models.UUIDField(_('UUID'), default=uuid.uuid4(), editable=False)
    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = "features"
        verbose_name = _("feature")
        verbose_name_plural = _("features")

    def __str__(self):
        return "%s" % self.name

    def clean(self):
        if self.map_dashboard:
            if self.geolocation is False:
                raise ValidationError(
                    {"geolocation": _("MAP Dashboard require GeoLocation feature!")}
                )

        if self.is_lte_signal:
            if self.mobile_connect is False:
                raise ValidationError(
                    {"mobile_connect": _("LTE Signal require Mobile Connect!")}
                )


class Organizations(models.Model):
    name = models.CharField(_("Name"), max_length=50, unique=True)
    controller = models.ForeignKey(
        Controllers, on_delete=models.SET_NULL, verbose_name=_("Controller"), null=True
    )
    features = models.ForeignKey(
        Features,
        on_delete=models.SET_NULL,
        verbose_name=(_("Features")),
        blank=True,
        null=True,
    )

    is_no_org = models.BooleanField(default=False)

    # uuid = models.UUIDField(_('UUID'), blank=True, null=True)
    # uuid = models.UUIDField(_('UUID'), default=uuid.uuid4(), editable=False)
    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, unique=True, editable=False)

    # site = models.ForeignKey(
    site = models.OneToOneField(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Site"),
        help_text=_(
            "If this organization refer to same site with other organization, leave it empty."
        ),
    )

    logo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Logo"),
        help_text=_("Brand logo used in login or throughout the site (512x128 pixels)"),
    )

    logo_dashboard = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Logo Dashboard"),
        help_text=_("Brand logo used in dashboard (512x512 pixels)"),
    )

    favicon = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="favicon",
        verbose_name=_("Favicon"),
        help_text=_("Favicon file with extension .ico"),
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = "organizations"
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return "%s" % self.name

    def save(self):
        if self.features is None:
            try:
                feature = Features.objects.get(id=1)
                self.features = feature
            except ObjectDoesNotExist:
                pass

        # if self.id is None:
        #    self.uuid = uuid.uuid4()
        return super(Organizations, self).save()


class User(AbstractUser):
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_("Organization"),
        blank=True,
        null=True,
    )


class GroupOrganizations(ClusterableModel):
    def limit_choice_no_org():
        return {"is_no_org": False}

    name = models.CharField(_("Name"), max_length=50, unique=True)
    main_org = models.ForeignKey(
        Organizations,
        on_delete=models.CASCADE,
        verbose_name=_("Main Organization"),
        limit_choices_to=limit_choice_no_org,
    )
    member_org = ParentalManyToManyField(
        "Organizations", related_name="member_org", limit_choices_to=limit_choice_no_org
    )

    class Meta:
        db_table = "group_organizations"
        verbose_name = _("Group Organization")
        verbose_name_plural = _("Group Organizations")

    def __str__(self):
        return f"{self.name}"

    def member_org_list(self):
        return ", ".join([x.name for x in self.member_org.all()])

    member_org_list.short_description = _("Member Organizations List")
