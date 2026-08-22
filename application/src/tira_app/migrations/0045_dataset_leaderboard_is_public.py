from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0044_dataset_evaluator_allow_network"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="leaderboard_is_public",
            field=models.BooleanField(default=True),
        ),
    ]
