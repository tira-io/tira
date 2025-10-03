from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Runs some playground command."""

    def handle(self, *args, **options):
        import io
        import zipfile

        from celery.app.control import Inspect
        from celery.result import AsyncResult
        from tira_worker import app, evaluate

        inspect: Inspect = app.control.inspect()
        workers = inspect.active()
        print(f"I found {len(workers)} active workers")
        for name, worker in workers.items():
            print(f"\t{name}")

        result: AsyncResult = evaluate.delay(
            run_id="2025-10-01-10-39-59", dataset="multi-author-analysis-20251001-training", task="task_1", team="maik"
        )

        zip_bytes = next(result.collect())[1]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            for entry in archive.filelist:
                with archive.open(entry) as f:
                    print("\n\n", entry.filename, "\n\n", f.read())

    def add_arguments(self, parser):
        pass
