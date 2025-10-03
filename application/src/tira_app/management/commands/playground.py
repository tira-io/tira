from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Runs some playground command."""

    def handle(self, *args, **options):
        from tira_app.endpoints.vm_api import run_sandboxed_eval

        print(
            run_sandboxed_eval(
                run_id="2025-10-03-13-19-56",
                dataset="multi-author-analysis-20251003-training",
                task="task_1",
                team="maik",
                join=True,
            )
        )

    def add_arguments(self, parser):
        pass
