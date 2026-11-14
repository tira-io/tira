from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tira", "0052_allow_network_access_on_request"),
    ]

    operations = [
        migrations.AddField(
            model_name="evaluator",
            name="output_format",
            field=models.CharField(default="prototext", max_length=100),
        ),
        migrations.AddField(
            model_name="evaluator",
            name="forward_environment_variable",
            field=models.TextField(default=None, null=True),
        ),
    ]
