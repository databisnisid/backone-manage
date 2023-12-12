# Generated by Django 4.2.4 on 2023-12-07 09:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0001_initial'),
        ('webfilters', '0005_alter_webfilters_domains_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webfilters',
            name='network',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='networks.networks', verbose_name='Network'),
        ),
    ]
