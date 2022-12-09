# Generated by Django 4.0.6 on 2022-12-09 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_features_ssh_features_web'),
    ]

    operations = [
        migrations.AlterField(
            model_name='features',
            name='authorize',
            field=models.BooleanField(default=False, verbose_name='Authorize'),
        ),
        migrations.AlterField(
            model_name='features',
            name='bridge',
            field=models.BooleanField(default=False, verbose_name='Bridge'),
        ),
        migrations.AlterField(
            model_name='features',
            name='ssh',
            field=models.BooleanField(default=False, verbose_name='Remote SSH'),
        ),
        migrations.AlterField(
            model_name='features',
            name='tags',
            field=models.BooleanField(default=False, verbose_name='Tags'),
        ),
        migrations.AlterField(
            model_name='features',
            name='web',
            field=models.BooleanField(default=False, verbose_name='Remote Web'),
        ),
    ]
