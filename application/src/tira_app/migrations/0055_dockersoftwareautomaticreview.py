import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0054_dockersoftwarereview"),
    ]

    operations = [
        migrations.CreateModel(
            name="DockerSoftwareAutomaticReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                (
                    "verdict",
                    models.CharField(
                        choices=[("no_concerns", "no_concerns"), ("needs_human_review", "needs_human_review")],
                        max_length=20,
                    ),
                ),
                ("comment", models.TextField(default="")),
                ("details", models.JSONField(default=dict)),
                ("uploader_id", models.CharField(max_length=150)),
                ("review_date", models.CharField(max_length=150)),
                ("archive_path", models.CharField(default="", max_length=500)),
                (
                    "docker_software",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="automatic_reviews",
                        to="tira.dockersoftware",
                    ),
                ),
            ],
        ),
    ]
