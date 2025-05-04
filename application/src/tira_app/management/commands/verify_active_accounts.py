import time

import requests
from django.core.management.base import BaseCommand
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

from ...model import DiscourseTokenForUser, Registration, Task
from ...tira_model import get_git_integration


def token_is_valid(token):
    from tempfile import TemporaryDirectory

    from tira.rest_api_client import Client

    with TemporaryDirectory() as tmp_dir:
        try:
            tira = Client(api_key=token, tira_cache_dir=tmp_dir)
            return tira.api_key_is_valid()
        except:
            return False


def verify_docker_credentials(team, token):
    from tempfile import TemporaryDirectory

    from tira.rest_api_client import Client

    with TemporaryDirectory() as tmp_dir:
        tira = Client(api_key=token, tira_cache_dir=tmp_dir)
        assert tira.api_key_is_valid()
        for r in Registration.objects.filter(team_name=team):
            if not r.registered_on_task:
                continue
            try:
                docker_credentials = tira.docker_credentials(r.registered_on_task.task_id, team)
            except:
                return False
            response = requests.get(
                "https://registry.webis.de/v2/", auth=HTTPBasicAuth(docker_credentials[0], docker_credentials[1])
            )
            return response.status_code == 200


class Command(BaseCommand):
    """Runs some playground command."""

    def handle(self, *args, **options):
        git_runner = get_git_integration("webis", None)
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

        for team in ["baseline"]:
            # repo = git_runner.existing_repository("tira-user-" + team)
            # print(repo.files.get("README.md", ref="main").decode().decode("UTF-8"))
            git_runner.create_user_repository(team, force_recreate=True)
        #           print(team, "->", verify_docker_credentials(team, team_to_token[team][0]))
        return

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

        invalid_docker_clients = set()
        for team in tqdm(team_to_token.keys(), "Test team docker credentials"):
            if not verify_docker_credentials(team, team_to_token[team][0]):
                invalid_docker_clients.add(team)

        print(f"{len(invalid_docker_clients)} invalid docker registries.")

    def add_arguments(self, parser):
        pass
