# Generated by Django 4.0.6 on 2022-08-22 10:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='members',
            name='peers',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.memberpeers', verbose_name='Peers'),
        ),
    ]