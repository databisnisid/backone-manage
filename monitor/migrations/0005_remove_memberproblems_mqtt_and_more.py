# Generated by Django 4.0.6 on 2023-01-09 09:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0004_memberproblems_organization_memberproblems_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='memberproblems',
            name='mqtt',
        ),
        migrations.RemoveField(
            model_name='memberproblems',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='memberproblems',
            name='user',
        ),
    ]