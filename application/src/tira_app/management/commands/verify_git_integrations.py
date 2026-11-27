from django.core.management.base import BaseCommand, CommandError

from ...git_runner import check_that_git_integration_is_valid
from ...model import GitIntegration


class Command(BaseCommand):
    """Verify that a stored git integration still has valid credentials.

    Looks up the persisted ``GitIntegration`` with the given namespace_url and checks it via
    ``check_that_git_integration_is_valid``.
    """

    help = "Verify that a stored git integration still has valid credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            "namespace_url",
            type=str,
            nargs="?",
            default="https://git.webis.de/code-research/tira",
            help="The namespace_url of the GitIntegration to verify.",
        )

    def handle(self, *args, **options):
        namespace_url = options["namespace_url"]

        print(namespace_url)
        try:
            git_integration = GitIntegration.objects.get(namespace_url=namespace_url)
        except GitIntegration.DoesNotExist:
            raise CommandError(f"No git integration found for namespace_url '{namespace_url}'.")

        print(git_integration)
        is_valid, message = check_that_git_integration_is_valid(
            git_integration.namespace_url, git_integration.private_token
        )

        if is_valid:
            self.stdout.write(self.style.SUCCESS(f"Git integration '{namespace_url}' is valid: {message}"))
        else:
            raise CommandError(f"Git integration '{namespace_url}' is invalid: {message}")
