# Generated by Django 4.2.11 on 2024-08-27 06:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zabbix', '0002_zabbixnetworks_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZabbixConfigs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('url', models.CharField(max_length=200, verbose_name='Zabbix API URL')),
                ('token', models.CharField(max_length=200, verbose_name='Zabbix Token')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Zabbix Config',
                'verbose_name_plural': 'Zabbix Configs',
                'db_table': 'zabbix_configs',
            },
        ),
        migrations.AddField(
            model_name='zabbixnetworks',
            name='config',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='zabbix.zabbixconfigs', verbose_name='Zabbix Config'),
        ),
    ]
