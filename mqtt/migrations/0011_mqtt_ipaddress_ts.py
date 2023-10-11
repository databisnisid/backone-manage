# Generated by Django 4.2.4 on 2023-10-11 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mqtt', '0010_mqtt_quota_vnstat'),
    ]

    operations = [
        migrations.AddField(
            model_name='mqtt',
            name='ipaddress_ts',
            field=models.GenericIPAddressField(blank=True, null=True, verbose_name='Tailscale IP'),
        ),
    ]
