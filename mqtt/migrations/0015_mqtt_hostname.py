# Generated by Django 4.2.11 on 2024-08-24 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mqtt', '0014_mqtt_rssi_signal'),
    ]

    operations = [
        migrations.AddField(
            model_name='mqtt',
            name='hostname',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Hostname'),
        ),
    ]
