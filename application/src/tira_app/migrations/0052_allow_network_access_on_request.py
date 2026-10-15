from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0051_task_export_buttons"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="allow_network_access_on_request",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dockersoftware",
            name="allow_network_access_on_request",
            field=models.BooleanField(default=False),
        ),
    ]
