import logging

from django.conf import settings

logger = logging.getLogger("tira")


def all_git_runners():
    from tira.tira_model import model

    ret = []
    for git_integration in model.all_git_integrations(return_dict=True):
        try:
            ret += [get_git_runner(git_integration)]
        except Exception:
            print(f"Could not load git integration: {git_integration}. Skip")
            logger.warn(f"Could not load git integration: {git_integration}. Skip")

    return ret


def get_git_runner(git_integration):
    from tira.git_runner_integration import GithubRunner, GitLabRunner

    if not git_integration or "namespace_url" not in git_integration:
        return None

    if "github.com" in git_integration["namespace_url"]:
        return GithubRunner(git_integration["private_token"])
    else:
        return GitLabRunner(
            git_integration["private_token"],
            git_integration["host"],
            git_integration["user_name"],
            git_integration["user_password"],
            git_integration["gitlab_repository_namespace_id"],
            git_integration["image_registry_prefix"],
            git_integration["user_repository_branch"],
        )


def get_git_runner_for_software_integration():
    from tira.git_runner_integration import GithubRunner

    return GithubRunner(settings.GITHUB_TOKEN)
