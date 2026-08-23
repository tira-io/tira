from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0043_task_hide_upload_via_cli"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="allow_network",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="evaluator",
            name="allow_network",
            field=models.BooleanField(default=False),
        ),
    ]
