# Generated by Django 4.0.6 on 2023-01-09 09:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0005_remove_memberproblems_mqtt_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberProblemsDone',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('monitor.memberproblems',),
        ),
    ]