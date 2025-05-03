import time

from django.core.management.base import BaseCommand
from tqdm import tqdm

from ...model import DiscourseTokenForUser, Registration, Task


def token_is_valid(token):
    from tempfile import TemporaryDirectory

    from tira.rest_api_client import Client

    with TemporaryDirectory() as tmp_dir:
        try:
            tira = Client(api_key=token, tira_cache_dir=tmp_dir)
            return tira.api_key_is_valid()
        except:
            return False


class Command(BaseCommand):
    """Runs some playground command."""

    def handle(self, *args, **options):
        teams = set()
        for t in Task.objects.all():
            if t and t.featured:
                for team in t.allowed_task_teams.split("\n"):
                    teams.add(team.strip())

        team_to_token = {}
        for team in tqdm(teams, "Load team tokens"):
            for token in DiscourseTokenForUser.objects.filter(vm_id__vm_id=team):
                if team and team not in team_to_token:
                    team_to_token[team] = []

                team_to_token[team].append(token.token)

        invalid_teams = set()
        for team in tqdm(team_to_token.keys(), "Test team tokens"):
            for token in team_to_token[team]:
                time.sleep(1)
                if not token_is_valid(token):
                    invalid_teams.add(team)

        print(f"{len(invalid_teams)} invalid teams.")
        for team in invalid_teams:
            print("\n" + team + "\n")
            for r in Registration.objects.filter(team_name=team):
                print(f"https://www.tira.io/submit/{r.registered_on_task.task_id}/user/{team}/code-submission")

    def add_arguments(self, parser):
        pass
