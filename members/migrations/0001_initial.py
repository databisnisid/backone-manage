# Generated by Django 4.0.6 on 2022-08-13 11:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import members.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('networks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberPeers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('peers', models.TextField(verbose_name='Peers')),
                ('member_id', models.CharField(max_length=50, verbose_name='Member ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='networks.networks', verbose_name='Network')),
            ],
            options={
                'verbose_name': 'member peer',
                'verbose_name_plural': 'member peers',
                'db_table': 'member_peers',
            },
        ),
        migrations.CreateModel(
            name='Members',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Member Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('member_id', models.CharField(max_length=50, verbose_name='Member ID')),
                ('is_bridge', models.BooleanField(default=False, verbose_name='Bridge')),
                ('is_authorized', models.BooleanField(default=True, verbose_name='Authorized')),
                ('ipaddress', models.CharField(blank=True, max_length=100, null=True, verbose_name='IP Address')),
                ('configuration', models.TextField(blank=True, verbose_name='Configuration')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('network', models.ForeignKey(limit_choices_to=members.models.Members.limit_choices_to_current_user, on_delete=django.db.models.deletion.CASCADE, to='networks.networks', verbose_name='Network')),
                ('peers', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.memberpeers', verbose_name='Peers')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Owner')),
            ],
            options={
                'verbose_name': 'member',
                'verbose_name_plural': 'members',
                'db_table': 'members',
            },
        ),
    ]
