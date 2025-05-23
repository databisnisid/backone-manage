# Generated by Django 4.2.19 on 2025-05-14 09:25

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0034_alter_organizations_site'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupOrganizations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Name')),
                ('main_org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.organizations', verbose_name='Main Organization')),
                ('member_org', modelcluster.fields.ParentalManyToManyField(related_name='member_org', to='accounts.organizations')),
            ],
            options={
                'verbose_name': 'Group Organization',
                'verbose_name_plural': 'Group Organizations',
                'db_table': 'group_organizations',
            },
        ),
    ]
