# Generated by Django 4.0.6 on 2023-01-11 04:46

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0007_memberproblems_duration'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='memberproblems',
            managers=[
                ('unsolved', django.db.models.manager.Manager()),
            ],
        ),
    ]
