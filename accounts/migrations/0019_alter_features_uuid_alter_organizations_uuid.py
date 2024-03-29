# Generated by Django 4.2.11 on 2024-03-07 15:07

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_alter_features_uuid_alter_organizations_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='features',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('83cecf43-8c1c-4fa5-b8d2-28de91922964'), editable=False, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='organizations',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('81c6339f-d63a-4fab-904b-04876fe01ed9'), editable=False, verbose_name='UUID'),
        ),
    ]
