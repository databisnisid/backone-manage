# Generated by Django 4.2.4 on 2023-09-15 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_features_map_dashboard'),
    ]

    operations = [
        migrations.AddField(
            model_name='features',
            name='is_nms',
            field=models.BooleanField(default=False, verbose_name='Monitoring'),
        ),
    ]
