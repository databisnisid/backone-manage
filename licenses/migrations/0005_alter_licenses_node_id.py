# Generated by Django 4.2.11 on 2024-03-12 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0004_alter_licenses_license_string'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licenses',
            name='node_id',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Node ID'),
        ),
    ]
