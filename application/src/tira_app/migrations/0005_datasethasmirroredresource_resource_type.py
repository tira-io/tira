# Generated by Django 5.0.9 on 2024-12-01 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tira", "0004_mirroredresource_datasethasmirroredresource"),
    ]

    operations = [
        migrations.AddField(
            model_name="datasethasmirroredresource",
            name="resource_type",
            field=models.CharField(default="inputs", max_length=15),
            preserve_default=False,
        ),
    ]
