from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0042_run_dynamic_mounts"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="hide_upload_via_cli",
            field=models.BooleanField(default=False),
        ),
    ]
