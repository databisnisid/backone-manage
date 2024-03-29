# Generated by Django 4.2.4 on 2023-12-07 04:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webfilters', '0003_alter_webfiltersmembers_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='webfilters',
            name='domains_white',
            field=models.TextField(blank=True, help_text='List top domain to allow', null=True, verbose_name='White List'),
        ),
        migrations.AddField(
            model_name='webfilters',
            name='is_default_block',
            field=models.BooleanField(default=False, help_text='CHeck this for block all website as default', verbose_name='Default Block All'),
        ),
        migrations.AlterField(
            model_name='webfilters',
            name='domains',
            field=models.TextField(help_text='List top domain to block', verbose_name='Black List'),
        ),
    ]
