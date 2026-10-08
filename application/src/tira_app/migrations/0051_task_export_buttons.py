from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0050_dockersoftware_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="export_buttons",
            field=models.TextField(default=None, null=True),
        ),
    ]
