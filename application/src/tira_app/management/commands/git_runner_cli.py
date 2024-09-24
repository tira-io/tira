import json
import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand
from slugify import slugify
from tqdm import tqdm

from ...tira_model import (
    add_input_run_id_to_all_rerank_runs,
    create_re_rank_output_on_dataset,
    get_git_integration,
    load_refresh_timestamp_for_cache_key,
)
from ...util import get_tira_id

logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run git_runner via cli.
    Later this will become a fully fledged cli tool that we use as wrapper in the repository.
    At the moment, we just execute some predefined commands
    """

    def run_command_create_user_repository(self, options, git_runner):
        print(f'Create a user repository for {options["create_user_repository"]}.')
        repo_id = git_runner.create_user_repository(options["create_user_repository"])
        print(f"The new repository has the id ${repo_id}")
        print(
            git_runner.add_new_tag_to_docker_image_repository(
                "registry.webis.de/code-research/tira/tira-user-del-maik-user-repo/my-software",
                "0.0.3",
                "0.0.1-tira-docker-software-id-name-x",
            )
        )
        print("Images: " + str(git_runner.docker_images_in_user_repository(options["create_user_repository"])))

    def run_command_create_task_repository(self, options, git_runner):
        print(f'Create a task-repository for {options["create_task_repository"]}.')
        repo_id = git_runner.create_task_repository(options["create_task_repository"])
        print(f"The new task-repository has the id ${repo_id}")

    def run_command_running_jobs(self, options, git_runner):
        if "user_id" not in options or not options["user_id"]:
            raise ValueError("Please pass --user_id as argument.")

        print(list(git_runner.yield_all_running_pipelines(options["running_jobs"], options["user_id"], cache, True)))

        print(load_refresh_timestamp_for_cache_key(cache, "all-running-pipelines-repo-" + options["running_jobs"]))

    def run_command_stop_job_and_clean_up(self, options, git_runner):
        if "user_id" not in options or not options["user_id"]:
            raise ValueError("Please pass --user_id as argument.")

        if "run_id" not in options or not options["run_id"]:
            raise ValueError("Please pass --run_id as argument.")

        git_runner.stop_job_and_clean_up(options["stop_job_and_clean_up"], options["user_id"], options["run_id"])

    def archive_repository_add_images_from_git_repo(self, options):
        from ... import model as modeldb

        with open(options["archive_repository_add_images_from_git_repo"], "r") as f:
            for line in tqdm(f):
                data = json.loads(line)
                if "docker-software-" not in data["TIRA_SOFTWARE_ID"]:
                    print("Skip")
                    continue

                docker_software_id = int(data["TIRA_SOFTWARE_ID"].split("docker-software-")[1])
                software = modeldb.DockerSoftware.objects.get(docker_software_id=docker_software_id)
                if (
                    data["TIRA_COMMAND_TO_EXECUTE"] != software.command
                    or not data["TIRA_IMAGE_TO_EXECUTE"].startswith(software.user_image_name)
                    or data["TIRA_IMAGE_TO_EXECUTE"] != software.tira_image_name
                ):
                    print("Skip")
                    continue

                software.public_image_name = data["TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB"]
                software.public_image_size = max(data["image_details"]["size"], data["image_details"]["virtual_size"])
                software.save()

    def archive_docker_software(self, approach, git_runner):
        from ... import model as modeldb
        from ...util import docker_image_details

        task_id, vm_id, name = approach.split("/")
        software = modeldb.DockerSoftware.objects.filter(
            vm__vm_id=vm_id, task__task_id=task_id, display_name=name, deleted=False
        )

        if len(software) != 1:
            raise ValueError(f"Found {software} but expected a single entry.")

        software = software[0]
        if software.public_image_name and software.public_image_size:
            print(f'Software "{approach}" is already public.')
            return

        print(software)
        image_name = (slugify(software.tira_image_name)).replace("/", "-")
        dockerhub_image = f"docker.io/webis/{task_id}-submissions:" + image_name.split("-tira-user-")[1].strip()

        software_definition = {
            "TIRA_IMAGE_TO_EXECUTE": software.tira_image_name,
            "TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB": dockerhub_image,
        }
        git_runner.archive_software(
            "/tmp/", software_definition, download_images=True, persist_images=False, upload_images=True
        )
        image_metadata = docker_image_details(software.tira_image_name)

        print(image_metadata)
        print(image_name)
        print(dockerhub_image)
        software.public_image_name = dockerhub_image
        software.public_image_size = image_metadata["size"]
        software.save()

    def handle(self, *args, **options):
        if "organization" not in options or not options["organization"]:
            raise ValueError("Please pass --organization")

        git_runner = get_git_integration(options["organization"], None)
        print(f"Use {git_runner}.")

        if "archive_repository" in options and options["archive_repository"]:
            git_runner.archive_repository(
                repo_name=options["archive_repository"],
                working_directory="./" + options["archive_repository"],
                download_images=options["archive_repository_download_images"].lower() == "true",
                persist_images=options["archive_repository_persist_images"].lower() == "true",
                upload_images=options["archive_repository_upload_images"].lower() == "true",
                persist_datasets=options["archive_repository_persist_datasets"].lower() == "true",
                copy_runs=options["archive_repository_copy_runs"].lower() == "true",
            )

        if "create_task_repository" in options and options["create_task_repository"]:
            self.run_command_create_task_repository(options, git_runner)

        if "create_user_repository" in options and options["create_user_repository"]:
            self.run_command_create_user_repository(options, git_runner)

        if "running_jobs" in options and options["running_jobs"]:
            self.run_command_running_jobs(options, git_runner)

        if "stop_job_and_clean_up" in options and options["stop_job_and_clean_up"]:
            self.run_command_stop_job_and_clean_up(options, git_runner)

        if (
            "archive_repository_add_images_from_git_repo" in options
            and options["archive_repository_add_images_from_git_repo"]
        ):
            self.archive_repository_add_images_from_git_repo(options)

        if "archive_docker_software" in options and options["archive_docker_software"]:
            self.archive_docker_software(options["archive_docker_software"], git_runner)

        if "run_image" in options and options["run_image"]:
            git_runner.start_git_workflow(
                task_id="clickbait-spoiling",
                dataset_id="task-1-type-classification-validation-20220924-training",
                vm_id="princess-knight",
                run_id=get_tira_id(),
                git_runner_image="webis/pan-clickbait-spoiling-evaluator:0.0.10",
                git_runner_command="bash -c '/clickbait-spoiling-eval.py --task 2 --ground_truth_spoiler $inputDataset --input_run $inputRun --output_prototext ${outputDir}/evaluation.prototext'",
                git_repository_id=2761,
                evaluator_id="task-2-spoiler-generation-validation-20220924-training-evaluator",
                user_image_to_execute="registry.webis.de/code-research/tira/tira-user-princess-knight/naive-baseline-task2:0.0.1-tira-docker-software-id-genteel-upstream",
                user_command_to_execute=(
                    "/naive-baseline-task-2.py --input $inputDataset/input.jsonl --output $outputDir/run.jsonl"
                ),
                tira_software_id="17",
                resources="small-resources-gpu",
            )

        if "clean_repository" in options and options["clean_repository"]:
            #            raise ValueError('ToDo: please insert the git authentication token with the name "tira-automation-bot-gitlab-admin-token" (maiks keepass) to git_runner.py method get_git_runner'
            git_runner.clean_task_repository(options["clean_repository"])

        if "docker_images_in_user_repository" in options and options["docker_images_in_user_repository"]:
            print(git_runner.docker_images_in_user_repository(options["docker_images_in_user_repository"]))

        if "rerank" in options and options["rerank"]:
            docker_software_id = 244  # "BM25 (tira-ir-starter-pyterrier)"
            # Execute once in k8s: ./manage.py git_runner_cli --organization webis --rerank true
            # Copy File
            # Comment out dataset id
            # configure ir-dataset: add ir_datasets image, ir_datasets re-ranking command, ir_datasets resources
            # For new datasets: INSERT INTO tira_dockersoftware (`command`, `display_name`, `user_image_name`, `tira_image_name`, `deleted`, `task_id`, `vm_id`, `description`, `paper_link`, `ir_re_ranker`, `ir_re_ranking_input`) VALUES ('tbd', 'Anserini MS-MARCO Dev', 'tbd', 'tbd', 0, 'reneuir-2024', 'froebe', 'tbd', '', 0, 1);
            # db statement: SELECT * FROM tira_run WHERE run_id LIKE '%rerank-%';
            # re-run with update re-ranking jobs
            datasets = [
                "cranfield-20230107-training",
                "antique-test-20230107-training",
                "vaswani-20230107-training",
                "msmarco-passage-trec-dl-2019-judged-20230107-training",
                "medline-2004-trec-genomics-2004-20230107-training",
                "wapo-v2-trec-core-2018-20230107-training",
                "cord19-fulltext-trec-covid-20230107-training",
                "disks45-nocr-trec7-20230209-training",
                "disks45-nocr-trec8-20230209-training",
                "disks45-nocr-trec-robust-2004-20230209-training",
                "nfcorpus-test-20230107-training",
                "argsme-touche-2020-task-1-20230209-training",
                "argsme-touche-2021-task-1-20230209-training",
                "msmarco-passage-trec-dl-2020-judged-20230107-training",
                "medline-2004-trec-genomics-2005-20230107-training",
                "gov-trec-web-2002-20230209-training",
                "gov-trec-web-2003-20230209-training",
                "gov-trec-web-2004-20230209-training",
                "gov2-trec-tb-2006-20230209-training",
                "gov2-trec-tb-2004-20230209-training",
                "gov2-trec-tb-2005-20230209-training",
                "medline-2017-trec-pm-2017-20230211-training",
                "medline-2017-trec-pm-2018-20230211-training",
                "clueweb12-trec-misinfo-2019-20240214-training",
                "longeval-heldout-20230513-training",
                "longeval-long-september-20230513-training",
                "longeval-short-july-20230513-training",
                "longeval-train-20230513-training",
                "trec-tip-of-the-tongue-dev-20230607-training",
                "longeval-2023-06-20240418-training",
                "longeval-2023-08-20240418-training",
                "ir-acl-anthology-topics-leipzig-20240423-test",
                "ir-acl-anthology-topics-leipzig-20240423-test",
                "ir-acl-anthology-topics-augsburg-20240525_0-test",
                "ir-acl-anthology-20240504-training",
                "ir-acl-anthology-topics-koeln-20240614-test",
                "ms-marco-100-queries-20240629-training",  # /mnt/ceph/tira/data/runs/ms-marco-100-queries-20240629-training/froebe/2024-06-30-22-13-09-rerank-2024-06-30-22-23-08
                "ms-marco-1000-queries-20240629-training",  # /mnt/ceph/tira/data/runs/ms-marco-1000-queries-20240629-training/froebe/2024-06-30-22-14-54-rerank-2024-06-30-23-07-44
                "ms-marco-all-dev-queries-20240629-training",  # /mnt/ceph/tira/data/runs/dl-top-10-docs-20240701-training/tira-ir-starter/2024-07-01-15-45-55-rerank-2024-07-02-10-40-56
                "dl-top-10-docs-20240701-training",  # /mnt/ceph/tira/data/runs/dl-top-10-docs-20240701-training/froebe/2024-07-01-15-45-55-rerank-2024-07-02-10-40-56
                "dl-top-100-docs-20240701-training",  # /mnt/ceph/tira/data/runs/dl-top-100-docs-20240701-training/tira-ir-starter/2024-07-01-15-46-44-rerank-2024-07-02-10-49-03
                "dl-top-1000-docs-20240701-training",  # /mnt/ceph/tira/data/runs/dl-top-1000-docs-20240701-training/froebe/2024-07-01-15-47-04-rerank-2024-07-02-10-53-30
            ]
            for dataset in datasets:
                print(dataset)
                tmp = create_re_rank_output_on_dataset(
                    task_id="ir-benchmarks",
                    vm_id="tira-ir-starter",
                    software_id=None,
                    docker_software_id=docker_software_id,
                    dataset_id=dataset,
                )
                if tmp:
                    print(f'/mnt/ceph/tira/data/runs/{tmp["dataset_id"]}/{tmp["vm_id"]}/{tmp["run_id"]}/')

            docker_software_id = 242  # "ChatNoir"
            datasets = [
                "clueweb09-en-trec-web-2009-20230107-training",
                "clueweb09-en-trec-web-2010-20230107-training",
                "clueweb09-en-trec-web-2011-20230107-training",
                "clueweb09-en-trec-web-2012-20230107-training",
                "clueweb12-trec-web-2013-20230107-training",
                "clueweb12-trec-web-2014-20230107-training",
                "clueweb12-touche-2020-task-2-20230209-training",
                "clueweb12-touche-2021-task-2-20230209-training",
            ]
            for dataset in datasets:
                print(dataset)
                tmp = create_re_rank_output_on_dataset(
                    task_id="ir-benchmarks",
                    vm_id="tira-ir-starter",
                    software_id=None,
                    docker_software_id=docker_software_id,
                    dataset_id=dataset,
                )
                if tmp:
                    print(f'/mnt/ceph/tira/data/runs/{tmp["dataset_id"]}/{tmp["vm_id"]}/{tmp["run_id"]}/')

            print(
                git_runner.extract_configuration_of_finished_job(
                    2979,
                    dataset_id="clinicaltrials-2017-trec-pm-2017-20230107-training",
                    vm_id="tira-ir-starter",
                    run_id="2023-01-12-15-02-11",
                )
            )

            print("\n\nReranking Datasets:\n\n")

            # for i in get_all_reranking_datasets(True).items():
            #    print(i)

            add_input_run_id_to_all_rerank_runs()

    def add_arguments(self, parser):
        parser.add_argument("--create_task_repository", default=None, type=str)
        parser.add_argument("--create_user_repository", default=None, type=str)
        parser.add_argument("--clean_repository", default=None, type=str)
        parser.add_argument("--run_image", default=None, type=str)
        parser.add_argument("--archive_repository", default=None, type=str)
        parser.add_argument("--archive_repository_download_images", default="false", type=str)
        parser.add_argument("--archive_repository_persist_images", default="false", type=str)
        parser.add_argument("--archive_repository_upload_images", default="false", type=str)
        parser.add_argument("--archive_repository_add_images_from_git_repo", default=None, type=str)
        parser.add_argument("--archive_docker_software", default=None, type=str)
        parser.add_argument("--archive_repository_persist_datasets", default="false", type=str)
        parser.add_argument("--archive_repository_copy_runs", default="false", type=str)
        parser.add_argument("--running_jobs", default=None, type=str)
        parser.add_argument("--stop_job_and_clean_up", default=None, type=str)
        parser.add_argument("--user_id", default=None, type=str)
        parser.add_argument("--run_id", default=None, type=str)
        parser.add_argument("--docker_images_in_user_repository", default=None, type=str)
        parser.add_argument("--organization", default=None, type=str)
        parser.add_argument("--rerank", default=None, type=str)
