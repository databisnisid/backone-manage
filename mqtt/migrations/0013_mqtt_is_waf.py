# Generated by Django 4.2.4 on 2023-10-30 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mqtt', '0012_mqtt_quota_first_prev'),
    ]

    operations = [
        migrations.AddField(
            model_name='mqtt',
            name='is_waf',
            field=models.BooleanField(default=False, verbose_name='WAF Running'),
        ),
    ]
