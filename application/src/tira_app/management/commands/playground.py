from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Runs some playground command."""

    def handle(self, *args, **options):
        from celery.app.control import Inspect
        from tira_worker import app, gpu_executor

        for i in [app, gpu_executor]:
            inspect: Inspect = i.control.inspect()
            workers = inspect.active()
            print(f"I found {len(workers)} {i} active workers:")
            for name, worker in workers.items():
                print(f"\t{name}", worker)

            workers = inspect.reserved()
            print(f"I found {len(workers)} {i} reserved workers:")
            for name, worker in workers.items():
                print(f"\t{name}", worker)

            workers = inspect.scheduled()
            print(f"I found {len(workers)} {i} scheduled workers:")
            for name, worker in workers.items():
                print(f"\t{name}", worker)

    def add_arguments(self, parser):
        pass
