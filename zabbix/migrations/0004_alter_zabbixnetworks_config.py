# Generated by Django 4.2.11 on 2024-08-27 06:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zabbix', '0003_zabbixconfigs_zabbixnetworks_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zabbixnetworks',
            name='config',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zabbix.zabbixconfigs', verbose_name='Zabbix Config'),
        ),
    ]
