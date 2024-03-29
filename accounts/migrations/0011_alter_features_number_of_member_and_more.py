# Generated by Django 4.2.4 on 2023-09-17 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_features_is_nms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='features',
            name='number_of_member',
            field=models.IntegerField(default=100, verbose_name='Number of Members'),
        ),
        migrations.AlterField(
            model_name='features',
            name='number_of_network',
            field=models.IntegerField(default=1, verbose_name='Number of Networks'),
        ),
    ]
