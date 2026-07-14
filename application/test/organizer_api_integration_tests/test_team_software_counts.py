from django.test import TestCase

import tira_app.model as modeldb
import tira_app.tira_model as tira_model


class TestTeamSoftwareCounts(TestCase):
    def test_count_of_team_software_reports_active_deleted_and_empty_teams(self):
        organizer = modeldb.Organizer.objects.create(organizer_id="orga", name="Organizer", years="2026", web="web")
        master_vm = modeldb.VirtualMachine.objects.create(vm_id="master-vm")
        team_a = modeldb.VirtualMachine.objects.create(vm_id="team-a")
        team_b = modeldb.VirtualMachine.objects.create(vm_id="team-b")
        modeldb.VirtualMachine.objects.create(vm_id="team-c")
        task = modeldb.Task.objects.create(
            task_id="task-1",
            task_name="Task 1",
            task_description="desc",
            vm=master_vm,
            organizer=organizer,
            web="web",
            allowed_task_teams="team-a\nteam-b\nteam-c",
        )

        modeldb.DockerSoftware.objects.create(vm=team_a, task=task, display_name="a-1", deleted=False)
        modeldb.DockerSoftware.objects.create(vm=team_a, task=task, display_name="a-2", deleted=False)
        modeldb.DockerSoftware.objects.create(vm=team_a, task=task, display_name="a-3", deleted=True)
        modeldb.DockerSoftware.objects.create(vm=team_b, task=task, display_name="b-1", deleted=True)
        modeldb.DockerSoftware.objects.create(vm=team_b, task=task, display_name="b-2", deleted=True)

        actual = {row["team"]: row for row in tira_model.get_count_of_team_software("task-1")}

        self.assertEqual(
            {
                "team-a": {
                    "team": "team-a",
                    "software_count": 2,
                    "deleted_software_count": 1,
                    "link": "https://www.tira.io/g/tira_vm_team-a",
                    "link_submission": "/submit/task-1/user/team-a",
                },
                "team-b": {
                    "team": "team-b",
                    "software_count": 0,
                    "deleted_software_count": 2,
                    "link": "https://www.tira.io/g/tira_vm_team-b",
                    "link_submission": "/submit/task-1/user/team-b",
                },
                "team-c": {
                    "team": "team-c",
                    "software_count": 0,
                    "deleted_software_count": 0,
                    "link": "https://www.tira.io/g/tira_vm_team-c",
                    "link_submission": "/submit/task-1/user/team-c",
                },
            },
            actual,
        )

    def test_count_of_team_software_executions_reports_dataset_usage(self):
        organizer = modeldb.Organizer.objects.create(organizer_id="orga", name="Organizer", years="2026", web="web")
        master_vm = modeldb.VirtualMachine.objects.create(vm_id="master-vm")
        team_a = modeldb.VirtualMachine.objects.create(vm_id="team-a")
        modeldb.VirtualMachine.objects.create(vm_id="team-b")
        task = modeldb.Task.objects.create(
            task_id="task-1",
            task_name="Task 1",
            task_description="desc",
            vm=master_vm,
            organizer=organizer,
            web="web",
            allowed_task_teams="team-a\nteam-b",
        )
        dataset_a = modeldb.Dataset.objects.create(dataset_id="dataset-a", display_name="Dataset A")
        dataset_b = modeldb.Dataset.objects.create(dataset_id="dataset-b", display_name="Dataset B")
        software_a_1 = modeldb.DockerSoftware.objects.create(
            vm=team_a, task=task, display_name="a-1", deleted=False
        )
        software_a_2 = modeldb.DockerSoftware.objects.create(
            vm=team_a, task=task, display_name="a-2", deleted=False
        )

        for run_id, software, dataset in [
            ("run-a-1-dataset-a", software_a_1, dataset_a),
            ("run-a-1-dataset-a-again", software_a_1, dataset_a),
            ("run-a-1-dataset-b", software_a_1, dataset_b),
            ("run-a-2-dataset-a", software_a_2, dataset_a),
        ]:
            modeldb.Run.objects.create(
                run_id=run_id,
                docker_software=software,
                input_dataset=dataset,
                task=task,
            )

        actual = tira_model.get_count_of_team_software_executions("task-1")

        self.assertEqual(
            [
                {
                    "team": "team-a",
                    "software": "a-1",
                    "software_id": software_a_1.docker_software_id,
                    "executed_on_unique_datasets": 2,
                    "executed_on_datasets": 3,
                    "link": "https://www.tira.io/g/tira_vm_team-a",
                    "link_submission": "/submit/task-1/user/team-a",
                },
                {
                    "team": "team-a",
                    "software": "a-2",
                    "software_id": software_a_2.docker_software_id,
                    "executed_on_unique_datasets": 1,
                    "executed_on_datasets": 1,
                    "link": "https://www.tira.io/g/tira_vm_team-a",
                    "link_submission": "/submit/task-1/user/team-a",
                },
            ],
            actual,
        )
