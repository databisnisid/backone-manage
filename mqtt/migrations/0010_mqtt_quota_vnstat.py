# Generated by Django 4.2.4 on 2023-09-14 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mqtt', '0009_mqtt_quota_first'),
    ]

    operations = [
        migrations.AddField(
            model_name='mqtt',
            name='quota_vnstat',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Quota VNStat'),
        ),
    ]