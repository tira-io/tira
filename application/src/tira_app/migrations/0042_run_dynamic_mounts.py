from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0041_task_upload_form_fields_upload_upload_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="dynamic_mounts",
            field=models.TextField(default=None, null=True),
        ),
    ]
