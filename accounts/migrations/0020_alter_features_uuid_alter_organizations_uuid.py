# Generated by Django 4.2.11 on 2024-03-07 15:21

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_alter_features_uuid_alter_organizations_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='features',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('a5c8b58c-5d75-457b-b3e3-8a425bb94bdb'), editable=False, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='organizations',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('49845266-b5a4-476d-9eb3-da3d804b37ff'), editable=False, verbose_name='UUID'),
        ),
    ]
