# Generated by Django 4.2.11 on 2024-09-10 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0012_members_is_waf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='members',
            name='mobile_number_first',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Mobile Number/Service Line'),
        ),
    ]
