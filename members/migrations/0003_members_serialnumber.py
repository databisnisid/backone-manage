# Generated by Django 4.0.6 on 2023-01-04 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_alter_members_peers'),
    ]

    operations = [
        migrations.AddField(
            model_name='members',
            name='serialnumber',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='SN'),
        ),
    ]
