# Generated by Django 4.2.11 on 2024-03-12 07:13

from django.db import migrations
from django.apps import apps
import uuid

def gen_uuid(apps, schema_editor):
    MyModel = apps.get_model("accounts", "Features")
    for row in MyModel.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=["uuid"])

    MyModel = apps.get_model("accounts", "Organizations")
    for row in MyModel.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=["uuid"])

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_features_uuid_organizations_uuid'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]
