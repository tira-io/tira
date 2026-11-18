import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0053_evaluator_output_format"),
    ]

    operations = [
        migrations.CreateModel(
            name="DockerSoftwareReview",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reviewer_id", models.CharField(max_length=150)),
                ("review_date", models.CharField(max_length=150)),
                (
                    "code_review",
                    models.CharField(
                        choices=[("pending", "pending"), ("approved", "approved"), ("rejected", "rejected")],
                        default="pending",
                        max_length=10,
                    ),
                ),
                (
                    "execution_review",
                    models.CharField(
                        choices=[("pending", "pending"), ("approved", "approved"), ("rejected", "rejected")],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("comment", models.TextField(default="")),
                (
                    "docker_software",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review",
                        to="tira.dockersoftware",
                    ),
                ),
            ],
        ),
    ]
