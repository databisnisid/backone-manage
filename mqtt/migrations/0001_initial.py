# Generated by Django 4.0.6 on 2022-12-12 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Mqtt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('member_id', models.CharField(max_length=50, verbose_name='Member ID')),
                ('model', models.CharField(blank=True, max_length=50, null=True, verbose_name='Model')),
                ('board_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='Board Name')),
                ('release_version', models.CharField(blank=True, max_length=50, null=True, verbose_name='Release Version')),
                ('release_target', models.CharField(blank=True, max_length=50, null=True, verbose_name='Release Target')),
                ('ipaddress', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP Address')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'MQTT',
                'verbose_name_plural': 'MQTT',
                'db_table': 'mqtt',
            },
        ),
    ]
