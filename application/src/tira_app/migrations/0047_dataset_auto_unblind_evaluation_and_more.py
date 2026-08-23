from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0046_remove_dataset_allow_network_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="auto_unblind_evaluation",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dataset",
            name="auto_unblind_runs",
            field=models.BooleanField(default=False),
        ),
    ]
