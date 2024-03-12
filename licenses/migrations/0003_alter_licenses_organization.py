# Generated by Django 4.2.11 on 2024-03-07 15:21

from django.db import migrations, models
import django.db.models.deletion
import licenses.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_alter_features_uuid_alter_organizations_uuid'),
        ('licenses', '0002_licenses_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licenses',
            name='organization',
            field=models.OneToOneField(blank=True, limit_choices_to=licenses.models.Licenses.limit_choices_to_org, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.organizations', verbose_name='Organization'),
        ),
    ]