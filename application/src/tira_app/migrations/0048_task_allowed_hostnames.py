from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0047_dataset_auto_unblind_evaluation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="allowed_hostnames",
            field=models.TextField(default=None, null=True),
        ),
    ]
