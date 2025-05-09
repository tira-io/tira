# Generated by Django 5.0.9 on 2025-03-11 19:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tira", "0015_dockersoftware_active_branch_dockersoftware_commit_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="dockersoftware",
            old_name="active_branch",
            new_name="source_code_active_branch",
        ),
        migrations.RenameField(
            model_name="dockersoftware",
            old_name="commit",
            new_name="source_code_commit",
        ),
        migrations.AddField(
            model_name="dockersoftware",
            name="try_run_metadata",
            field=models.ForeignKey(
                default=None, null=True, on_delete=django.db.models.deletion.RESTRICT, to="tira.anonymousuploads"
            ),
        ),
    ]
