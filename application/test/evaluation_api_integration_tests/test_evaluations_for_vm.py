import re

from api_access_matrix import ADMIN
from django.test import TestCase
from utils_for_testing import method_for_url_pattern, mock_request, now, set_up_tira_filesystem

import tira.model as modeldb
from tira.tira_model import model as tira_model

url = "api/evaluations-of-vm/<str:task_id>/<str:vm_id>"
evaluations_function = method_for_url_pattern(url)


PARTICIPANT_1 = "vm-eval-p1"
PARTICIPANT_2 = "vm-eval-p2"
PARTICIPANT_3 = "vm-eval-p3"
PARTICIPANT_4 = "vm-eval-p4"
PARTICIPANT_5 = "vm-eval-p5"
TASK = "vm-eval-task"
SOFTWARE_PARTICIPANT_1 = f"s-{PARTICIPANT_1}"
SOFTWARE_PARTICIPANT_2 = f"s-{PARTICIPANT_2}"
SOFTWARE_PARTICIPANT_3 = f"s-{PARTICIPANT_3}"
SOFTWARE_PARTICIPANT_4 = f"s-{PARTICIPANT_4}"
SOFTWARE_PARTICIPANT_5 = f"s-{PARTICIPANT_5}"
UPLOAD_PARTICIPANT_1 = f"u-{PARTICIPANT_1}"
SOFTWARES = {}
SOFTWARE_IDS = {}
UPLOAD = None


class TestEvaluationsForVm(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_filesystem()
        tira_model.edit_organizer("vm-eval-organizer", "organizer", "years", "web", [])
        tira_model.add_vm("master-vm-for-vm-eval-task", "user_name", "initial_user_password", "ip", "host", "12", "12")
        tira_model.create_task(
            TASK,
            "task_name",
            "task_description",
            False,
            "master-vm-for-vm-eval-task",
            "vm-eval-organizer",
            "website",
            False,
            False,
            False,
            "help_command",
            "",
            "",
        )
        evaluator = modeldb.Evaluator.objects.update_or_create(evaluator_id=f"{TASK}-evaluator")[0]

        datasets = []
        for d in ["vm-eval-task-1", "vm-eval-task-2", "vm-eval-task-3"]:
            d_type = "training" if d.endswith("-2") else "test"
            tira_model.add_dataset(TASK, d, d_type, d, "upload-name")
            datasets += [modeldb.Dataset.objects.get(dataset_id=f"{d}-{now}-{d_type}")]

        k_1 = 2.0
        k_2 = 1.0
        for participant in [PARTICIPANT_1, PARTICIPANT_2]:
            tira_model.add_vm(participant, "user_name", "initial_user_password", "ip", "host", "12", "12")

            SOFTWARES[f"s-{participant}"] = modeldb.DockerSoftware.objects.create(
                display_name=f"s-{participant}",
                vm=modeldb.VirtualMachine.objects.get(vm_id=participant),
                task=modeldb.Task.objects.get(task_id=TASK),
                deleted=False,
            )
            SOFTWARE_IDS[f"s-{participant}"] = str(int(SOFTWARES[f"s-{participant}"].docker_software_id))

            for d in datasets:
                run_id = f"{participant}-{d.dataset_id}"
                run = modeldb.Run.objects.create(
                    run_id=run_id,
                    software=None,
                    evaluator=None,
                    upload=None,
                    docker_software=SOFTWARES[f"s-{participant}"],
                    input_dataset=d,
                    task=modeldb.Task.objects.get(task_id=TASK),
                )

                eval_run = modeldb.Run.objects.create(
                    run_id=f"{run_id}-eval", input_run=run, input_dataset=d, evaluator=evaluator
                )
                # SOFTWARE_PARTICIPANT_1's runs are unblinded and published
                modeldb.Review.objects.create(
                    run=eval_run, published=participant == PARTICIPANT_1, blinded=participant != PARTICIPANT_1
                )

                modeldb.Review.objects.update_or_create(
                    run_id=run_id,
                    defaults={"published": participant == PARTICIPANT_1, "blinded": participant != PARTICIPANT_1},
                )

                modeldb.Evaluation.objects.create(measure_key="k-1", measure_value=k_1, run=eval_run)
                modeldb.Evaluation.objects.create(measure_key="k-2", measure_value=k_2, run=eval_run)
                k_1 -= 0.1
                k_2 += 0.1

        global UPLOAD
        UPLOAD = modeldb.Upload.objects.create(
            vm=modeldb.VirtualMachine.objects.get(vm_id=PARTICIPANT_1),
            task=modeldb.Task.objects.get(task_id=TASK),
            last_edit_date="1",
        )

        for d in datasets:
            run_id = f"{participant}-{d.dataset_id}-upload"
            run = modeldb.Run.objects.create(
                run_id=run_id,
                software=None,
                evaluator=None,
                upload=UPLOAD,
                docker_software=None,
                input_dataset=d,
                task=modeldb.Task.objects.get(task_id=TASK),
            )

        for participant in [PARTICIPANT_3, PARTICIPANT_4]:
            tira_model.add_vm(participant, "user_name", "initial_user_password", "ip", "host", "12", "12")

            SOFTWARES[f"s-{participant}"] = modeldb.DockerSoftware.objects.create(
                display_name=f"s-{participant}",
                vm=modeldb.VirtualMachine.objects.get(vm_id=participant),
                task=modeldb.Task.objects.get(task_id=TASK),
                deleted=False,
            )
            SOFTWARE_IDS[f"s-{participant}"] = str(int(SOFTWARES[f"s-{participant}"].docker_software_id))

            for i in range(3):
                d = datasets[0]
                run_id = f"{participant}-{d.dataset_id}-{i}"
                run = modeldb.Run.objects.create(
                    run_id=run_id,
                    software=None,
                    evaluator=None,
                    upload=None,
                    docker_software=SOFTWARES[f"s-{participant}"],
                    input_dataset=d,
                    task=modeldb.Task.objects.get(task_id=TASK),
                )

                eval_run = modeldb.Run.objects.create(
                    run_id=f"{run_id}-eval", input_run=run, input_dataset=d, evaluator=evaluator
                )
                # run 3 is published
                modeldb.Review.objects.create(
                    run=eval_run, published=i == 2 and PARTICIPANT_3 == participant, blinded=True
                )

                modeldb.Review.objects.update_or_create(
                    run_id=run_id, defaults={"published": i == 2 and PARTICIPANT_3 == participant, "blinded": True}
                )

                modeldb.Evaluation.objects.create(measure_key="k-1", measure_value=k_1, run=eval_run)
                modeldb.Evaluation.objects.create(measure_key="k-2", measure_value=k_2, run=eval_run)
                k_1 -= 0.1
                k_2 += 0.1

        for participant in [PARTICIPANT_5]:
            tira_model.add_vm(participant, "user_name", "initial_user_password", "ip", "host", "12", "12")

            SOFTWARES[f"s-{participant}"] = modeldb.DockerSoftware.objects.create(
                display_name=f"s-{participant}",
                vm=modeldb.VirtualMachine.objects.get(vm_id=participant),
                task=modeldb.Task.objects.get(task_id=TASK),
                deleted=False,
            )
            SOFTWARE_IDS[f"s-{participant}"] = str(int(SOFTWARES[f"s-{participant}"].docker_software_id))

            for i in range(3):
                d = datasets[0]
                run_id = f"{participant}-{d.dataset_id}-{i}"
                run = modeldb.Run.objects.create(
                    run_id=run_id,
                    software=None,
                    evaluator=None,
                    upload=None,
                    docker_software=SOFTWARES[f"s-{participant}"],
                    input_dataset=d,
                    task=modeldb.Task.objects.get(task_id=TASK),
                )

                eval_run = modeldb.Run.objects.create(
                    run_id=f"{run_id}-eval", input_run=run, input_dataset=d, evaluator=evaluator
                )
                modeldb.Review.objects.create(run=eval_run, published=False, blinded=True)
                modeldb.Review.objects.update_or_create(run_id=run_id, defaults={"published": False, "blinded": True})

    def test_existing_upload_of_for_user_with_all_published(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_1, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        global UPLOAD
        request.GET["upload_id"] = str(UPLOAD.id)

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_1)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_upload_submission.json")

    def test_for_non_existing_docker_software(self):
        # Arrange
        request = mock_request(ADMIN, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"})
        request.GET["docker_software_id"] = "-1212"

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_1)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_non_existing_task_and_dataset.json")

    def test_existing_docker_software_of_wrong_user_01(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_2, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_1]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_2)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_of_wrong_user_01.json")

    def test_existing_docker_software_of_wrong_user_02(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_1, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_2]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_1)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_of_wrong_user_02.json")

    def test_existing_docker_software_of_for_user_with_all_published(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_1, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_1]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_1)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_with_all_published.json")

    def test_existing_docker_software_of_for_user_with_one_published_on_train_data(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_2, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_2]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_2)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_with_one_published.json")

    def test_existing_docker_software_of_for_user_with_one_published_on_test_data(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_3, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_3]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_3)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_with_one_published_on_test_data.json")

    def test_existing_docker_software_of_for_user_with_none_published_on_test_data(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_4, url, params={"task_id": "<str:task_id>", "vm_id": "<str:vm_id>"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_4]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_4)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_with_none_published_on_test_data.json")

    def test_existing_docker_software_of_for_user_with_none_published_on_test_data_and_no_evaluations(self):
        # Arrange
        request = mock_request(
            "tira_vm_" + PARTICIPANT_5, url, params={"task_id": "does-not-exist", "vm_id": "does-not-exist"}
        )
        request.GET["docker_software_id"] = SOFTWARE_IDS[SOFTWARE_PARTICIPANT_5]

        # Act
        actual = evaluations_function(request, task_id=TASK, vm_id=PARTICIPANT_5)

        # Assert
        self.verify_as_json(actual, "vm_eval_for_existing_docker_software_with_none_published_on_test_data_no_ev.json")

    def verify_as_json(self, actual, test_name):
        import json

        from approvaltests import verify_as_json
        from approvaltests.core.options import Options
        from approvaltests.namer.cli_namer import CliNamer

        content = json.loads(actual.content)

        if "context" in content and "dataset_id" in content["context"]:
            content["context"]["dataset_id"] = content["context"]["dataset_id"].split("-20")[0]

        if "context" in content and "evaluations" in content["context"]:
            for i in content["context"]["evaluations"]:
                if "dataset_id" in i:
                    i["dataset_id"] = i["dataset_id"].split("-20")[0]

        if "context" in content and "runs" in content["context"]:
            for i in content["context"]["runs"]:
                if "dataset_id" in i:
                    i["dataset_id"] = i["dataset_id"].split("-20")[0]

                if "run_id" in i:
                    i["run_id"] = re.split(r"\d\d\d\d\d\d\d\d", i["run_id"])
                    i["run_id"] = i["run_id"][0] + "<TIME>" + i["run_id"][1]

                for t in ["link_results_download", "link_run_download"]:
                    if t in i:
                        i[t] = i[t].split("/dataset/")[0] + "/dataset/<TIME>/download/" + i[t].split("/download/")[1]
                        split = re.split(r"\d\d\d\d\d\d\d\d", i[t])
                        i[t] = split[0] + "<TIME>" + split[1]

        self.assertEqual(200, actual.status_code)
        verify_as_json(content, options=Options().with_namer(CliNamer(test_name)))

    @classmethod
    def tearDownClass(cls):
        pass
