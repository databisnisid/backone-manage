# Generated by Django 4.2.4 on 2023-09-13 04:32

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0008_alter_memberproblems_managers'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('member_problems', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_problems', to='monitor.memberproblems')),
            ],
            options={
                'db_table': 'problem_update',
            },
        ),
    ]