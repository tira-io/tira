from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0048_task_allowed_hostnames"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="task_export_metadata",
            field=models.TextField(default=None, null=True),
        ),
    ]
