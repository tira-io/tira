from datetime import datetime

from utils_for_testing import route_to_test, software_non_public, software_public

# Used for some tests
now = datetime.now().strftime("%Y%m%d")

ADMIN = "tira_reviewer"
GUEST = ""
PARTICIPANT = "tira_vm_PARTICIPANT-FOR-TEST-1"
ORGANIZER = "tira_org_EXAMPLE-ORGANIZER"
ORGANIZER_WRONG_TASK = "tira_org_ORGANIZER-FOR-OTHER-TASK"


API_ACCESS_MATRIX = [
    route_to_test(
        url_pattern="api/tirex-components",
        params=None,
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/tirex-snippet",
        params=None,
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/list-runs/<str:task_id>/<str:dataset_id>/<str:vm_id>/<str:software_id>",
        params={"task_id": "1", "dataset_id": 1, "vm_id": "1", "software_id": "1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/re-ranking-datasets/<str:task_id>",
        params={"task_id": "1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/public-submissions",
        params={"task_id": "1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/submission-details/<str:user_id>/<str:display_name>",
        params={"task_id": "1", "user_id": "2", "display_name": "3"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/submissions-of-user/<str:vm_id>",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/import-submission/<str:task_id>/<str:vm_id>/<str:submission_type>/<str:s_id>",
        params={"vm_id": "does-not-exist", "task_id": "does-not-exist", "submission_type": "1", "s_id": "1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip",
        params={
            "task_id": "shared-task-1",
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": "example_participant",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="data-download/git-repo-template/<str:vm_id>/<str:task_id>.zip",
        params={"task_id": "does-not-exist", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="data-download/<str:dataset_type>/<str:input_type>/<str:dataset_id>.zip",
        params={"dataset_type": "training", "dataset_id": f"dataset-1-{now}-training", "input_type": "input-"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="data-download/<str:dataset_type>/<str:input_type>/<str:dataset_id>.zip",
        params={
            "dataset_type": "training",
            "dataset_id": f"dataset-not-published-{now}-training",
            "input_type": "input-",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="data-download/<str:dataset_type>/<str:input_type>/<str:dataset_id>.zip",
        params={"dataset_type": "training", "dataset_id": f"dataset-2-{now}-test", "input_type": "input-"},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="data-download/<str:dataset_type>/<str:input_type>/<str:dataset_id>.zip",
        params={
            "dataset_type": "training",
            "dataset_id": f"dataset-of-organizer-{now}-training",
            "input_type": "input-",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/count-of-team-submissions/<str:task_id>",
        params={"task_id": "task-of-organizer-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/token/<str:vm_id>",
        params={"vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/add_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/add_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/add_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        params={"task_id": "does-not-exist", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/get_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/get_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/get_software_submission_git_repository/<str:task_id>/<str:vm_id>",
        params={"task_id": "does-not-exist", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/configuration-of-evaluation/<str:task_id>/<str:dataset_id>",
        params={"task_id": "shared-task-1", "dataset_id": f"dataset-1-{now}-training"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="diffir/<str:task_id>/<int:topk>/<str:run_id_1>/<str:run_id_2>",
        params={"task_id": "shared-task-1", "topk": 10, "run_id_1": "1", "run_id_2": "2"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip",
        params={
            "task_id": "shared-task-1",
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": PARTICIPANT.split("_")[-1],
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/huggingface_model_mounts/vm/<str:vm_id>/<str:hf_model>",
        params={"hf_model": "does-not-exist", "vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/huggingface_model_mounts/vm/<str:vm_id>/<str:hf_model>",
        params={"hf_model": "does-not-exist", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip",
        params={
            "task_id": "shared-task-1",
            "dataset_id": f"dataset-2-{now}-test",
            "vm_id": "example_participant",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/download/<str:run_id>.zip",
        params={
            "task_id": "shared-task-1",
            "dataset_id": f"dataset-2-{now}-test",
            "vm_id": PARTICIPANT.split("_")[-1],
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="serp/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/<int:topk>/<str:run_id>",
        params={
            "task_id": "shared-task-1",
            "topk": 10,
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": PARTICIPANT.split("_")[-1],
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="serp/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/<int:topk>/<str:run_id>",
        params={
            "task_id": "shared-task-1",
            "topk": 10,
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": "participant-1",
            "run_id": "run-1-participant-1",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="serp/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/<int:topk>/<str:run_id>",
        params={
            "task_id": "shared-task-1",
            "dataset_id": f"dataset-2-{now}-test",
            "topk": 10,
            "vm_id": "example_participant",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="serp/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/<int:topk>/<str:run_id>",
        params={
            "task_id": "shared-task-1",
            "dataset_id": f"dataset-2-{now}-test",
            "topk": 10,
            "vm_id": PARTICIPANT.split("_")[-1],
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/count-of-missing-reviews/<str:task_id>",
        params={"task_id": "shared-task-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="background_jobs/<str:task_id>/<str:job_id>",
        params={"task_id": "does-not-exist", "job_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="background_jobs/<str:task_id>/<str:job_id>",
        params={"task_id": "task-of-organizer-1", "job_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/docker",
        params={"task_id": "shared-task-1", "vm_id": "example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/docker",
        params={"task_id": "task-of-organizer-1", "vm_id": "example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/docker",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/software_details/<str:software_name>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "software_name": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/software_details/<str:software_name>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "software_name": software_non_public},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/software_details/<str:software_name>",
        params={"task_id": "shared-task-1", "vm_id": "PARTICIPANT-FOR-TEST-1", "software_name": software_public},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/software_details/<str:software_name>",
        params={"task_id": "shared-task-1", "vm_id": "PARTICIPANT-FOR-TEST-1", "software_name": software_non_public},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/upload-group-details/<str:task_id>/<str:vm_id>/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "upload_id": "10"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/upload",
        params={"task_id": "shared-task-1", "vm_id": "example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/upload",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/upload-delete/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": "does-not-exist", "upload_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/upload-delete/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1], "upload_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/upload/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": "does-not-exist", "upload_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/upload/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1], "upload_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "docker_software_id": 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/docker/<str:docker_software_id>",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1], "docker_software_id": 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "software_id": 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1], "software_id": 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": "example_participant", "software_id": 0},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/run_details/<str:run_id>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "run_id": "run-1-example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/run_details/<str:run_id>",
        params={"task_id": "shared-task-1", "vm_id": "participant-1", "run_id": "run-9-participant-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/software_details/<str:software_name>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "software_name": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant", "dataset_id": 0, "upload_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/upload/<str:dataset_id>/<str:upload_id>",
        params={"task_id": "shared-task-1", "vm_id": PARTICIPANT.split("_")[-1], "dataset_id": 0, "upload_id": -1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/evaluations_of_run/<str:vm_id>/<str:run_id>",
        params={"vm_id": PARTICIPANT.split("_")[-1], "run_id": "run-1-example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
        },
    ),
    route_to_test(
        url_pattern="api/evaluations_of_run/<str:vm_id>/<str:run_id>",
        params={"vm_id": "does-not-exist", "run_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
        },
    ),
    route_to_test(
        url_pattern="grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>/<str:rerank_dataset>",
        params={
            "task_id": "shared-task-1",
            "vm_id": "does-not-exist",
            "dataset_id": "does-not-exist",
            "docker_software_id": "does-not-exist",
            "rerank_dataset": "none",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>/<str:rerank_dataset>",
        params={
            "task_id": "shared-task-1",
            "vm_id": PARTICIPANT.split("_")[-1],
            "dataset_id": "does-not-exist",
            "docker_software_id": "does-not-exist",
            "rerank_dataset": "none",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>",
        params={
            "vm_id": "does-not-exist",
            "dataset_id": f"dataset-1-{now}-training",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # TODO Add later
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/run_eval/<str:dataset_id>/<str:run_id>',
    #    params={'vm_id': PARTICIPANT.split('_')[-1], 'dataset_id': f'dataset-1-{now}-training', 'run_id': 'run-1-example_participant'},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>",
        params={"user_id": "does-not-exist", "task_id": "does-not-exist", "submission_type": "does-not-matter"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>",
        params={
            "user_id": PARTICIPANT.split("_")[-1],
            "task_id": "shared-task-1",
            "submission_type": "does-not-matter",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/docker-softwares-details/<str:vm_id>/<str:docker_software_id>",
        params={"vm_id": PARTICIPANT.split("_")[-1], "docker_software_id": "1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/docker-softwares-details/<str:vm_id>/<str:docker_software_id>",
        params={
            "vm_id": "does-not-exist",
            "docker_software_id": "1",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="grpc/<str:task_id>/<str:user_id>/stop_docker_software/<str:run_id>",
        params={"user_id": "example_participant", "task_id": "shared-task-1", "run_id": "run-1-example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # Was error
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="grpc/<str:task_id>/<str:user_id>/stop_docker_software/<str:run_id>",
        params={
            "user_id": PARTICIPANT.split("_")[-1],
            "task_id": "shared-task-1",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-task/<str:task_id>",
        params={"task_id": "shared-task-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-task/<str:task_id>",
        params={"task_id": "task-of-organizer-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/delete-task/<str:task_id>",
        params={"task_id": "task-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/add-dataset/<str:task_id>",
        params={"task_id": "task-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/add-dataset/<str:task_id>",
        params={"task_id": "shared-task-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/add-dataset/<str:task_id>",
        params={"task_id": "task-of-organizer-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/upload-dataset/<str:task_id>/<str:dataset_id>/<str:dataset_type>",
        params={"task_id": "task-does-not-exist", "dataset_id": "does-not-exist", "dataset_type": "participant-input"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/upload-dataset/<str:task_id>/<str:dataset_id>/<str:dataset_type>",
        params={"task_id": "task-of-organizer-1", "dataset_id": "does-not-exist", "dataset_type": "participant-input"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-dataset/<str:dataset_id>",
        params={"dataset_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-dataset/<str:dataset_id>",
        params={"dataset_id": f"dataset-of-organizer-{now}-training"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-dataset/<str:dataset_id>",
        params={"dataset_id": f"dataset-1-{now}-training"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/delete-dataset/<str:dataset_id>",
        params={"dataset_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": "dataset-does-not-exist",
            "vm_id": "vm-id-does-not-exist",
            "run_id": "run-id-does-not-exist",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-of-organizer-{now}-training",
            "vm_id": "vm-id-does-not-exist",
            "run_id": "run-of-organizer",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-of-organizer-{now}-training",
            "vm_id": "vm-id-does-not-exist",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": "vm-id-does-not-exist",
            "run_id": "run-of-organizer",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="publish/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>",
        params={
            "dataset_id": "dataset-does-not-exist",
            "vm_id": "vm-id-does-not-exist",
            "run_id": "run-id-does-not-exist",
            "value": "does-not-exist",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO: Make consistent.
            PARTICIPANT: 302,  # TODO: Make consistent.
            ORGANIZER: 302,  # TODO: Make consistent.
            ORGANIZER_WRONG_TASK: 302,  # TODO: Make consistent.
        },
    ),
    route_to_test(
        url_pattern="blind/<str:vm_id>/<str:dataset_id>/<str:run_id>/<str:value>",
        params={
            "dataset_id": "dataset-does-not-exist",
            "vm_id": "vm-id-does-not-exist",
            "run_id": "run-id-does-not-exist",
            "value": "does-not-exist",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/evaluations/<str:task_id>/<str:dataset_id>",
        params={"task_id": "task-does-not-exist", "dataset_id": "dataset-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/evaluations-of-vm/<str:task_id>/<str:vm_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/evaluations-of-vm/<str:task_id>/<str:vm_id>",
        params={"task_id": "task-of-organizer-1", "vm_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/submissions/<str:task_id>/<str:dataset_id>",
        params={"task_id": "task-id-does-not-exist", "dataset_id": "dataset-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,  # TODO: Add more fine-grained tests, as admin gets different response
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/task-list",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>",
        params={"task_id": "task-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/registration_formular/<str:task_id>",
        params={"task_id": "task-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/dataset/<str:dataset_id>",
        params={"dataset_id": "dataset-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/datasets_by_task/<str:task_id>",
        params={"task_id": "task-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/role",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/user/<str:user_id>",
        params={"task_id": "task-id-does-not-exist", "user_id": "user-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            PARTICIPANT: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER_WRONG_TASK: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/user/<str:user_id>",
        params={"task_id": "task-id-does-not-exist", "user_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            PARTICIPANT: 200,
            ORGANIZER: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER_WRONG_TASK: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/user/<str:user_id>/refresh-docker-images",
        params={"task_id": "task-id-does-not-exist", "user_id": "user-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            PARTICIPANT: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER_WRONG_TASK: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/user/<str:user_id>/refresh-docker-images",
        params={"task_id": "task-id-does-not-exist", "user_id": PARTICIPANT.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            PARTICIPANT: 200,
            ORGANIZER: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER_WRONG_TASK: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/user/<str:user_id>/software/running/<str:force_cache_refresh>",
        params={
            "task_id": "task-id-does-not-exist",
            "user_id": "user-id-does-not-exist",
            "force_cache_refresh": "ignore",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            PARTICIPANT: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER_WRONG_TASK: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern="api/task/<str:task_id>/user/<str:user_id>/software/running/<str:force_cache_refresh>",
        params={
            "task_id": "task-id-does-not-exist",
            "user_id": PARTICIPANT.split("_")[-1],
            "force_cache_refresh": "ignore",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            PARTICIPANT: 200,
            ORGANIZER: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
            ORGANIZER_WRONG_TASK: 200,  # TODO: This seems to be wrong, but I am not sure, I would expect a 405 here.
        },
    ),
    route_to_test(
        url_pattern="api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": "dataset-id-does-not-exist",
            "vm_id": "example_participant",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": "example_participant",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-1-{now}-training",
            "vm_id": PARTICIPANT.split("_")[-1],
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 200,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-of-organizer-{now}-training",
            "vm_id": "does-not-exist",
            "run_id": "run-of-organizer",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
            PARTICIPANT: 302,  # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 302,  # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
        },
    ),
    route_to_test(
        url_pattern="api/review/<str:dataset_id>/<str:vm_id>/<str:run_id>",
        params={
            "dataset_id": f"dataset-of-organizer-{now}-training",
            "vm_id": "does-not-exist",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
            PARTICIPANT: 302,
            # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
            ORGANIZER: 302,  # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
            ORGANIZER_WRONG_TASK: 302,
            # TODO: Is this inconsistent with api/review/<str:dataset_id>/<str:vm_id>/<str:run_id> above?
        },
    ),
    route_to_test(
        url_pattern="tira-admin/<str:organizer_id>/create-task",
        params={"organizer_id": "organizer-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 501,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/<str:organizer_id>/create-task",
        params={"organizer_id": ORGANIZER.split("_")[-1]},
        group_to_expected_status_code={
            ADMIN: 501,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 501,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/registration/add_registration/<str:vm_id>/<str:task_id>",
        params={"task_id": "shared-task-1", "vm_id": "example_participant"},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 500,  # TODO: Would we expect an 404 here?
            PARTICIPANT: 500,  # TODO: Would we expect an 404 here?
            ORGANIZER: 500,  # TODO: Would we expect an 404 here?
            ORGANIZER_WRONG_TASK: 500,  # TODO: Would we expect an 404 here?
        },
        body='{"group": "X"}',
    ),
    # Some commands that delete stuff must be executed as last
    route_to_test(
        url_pattern="grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>",
        params={
            "vm_id": "does-not-exist",
            "dataset_id": f"dataset-1-{now}-training",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 202,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/run_delete/<str:dataset_id>/<str:run_id>",
        params={
            "vm_id": PARTICIPANT.split("_")[-1],
            "dataset_id": f"dataset-1-{now}-training",
            "run_id": "run-1-example_participant",
        },
        group_to_expected_status_code={
            ADMIN: 202,
            GUEST: 302,
            PARTICIPANT: 202,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/delete-task/<str:task_id>",
        params={"task_id": "task-of-organizer-1"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/delete-dataset/<str:dataset_id>",
        params={"dataset_id": f"dataset-of-organizer-{now}-training"},
        group_to_expected_status_code={
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER_WRONG_TASK: 405,
            ORGANIZER: 200,
        },
    ),
]


def access_matrix_for_user(user):
    ret = []
    for i in API_ACCESS_MATRIX:
        if user not in i[2]:
            continue
        params = i[2][user]["params"]
        expected_status_code = i[2][user]["expected_status_code"]

        ret += [(i[0], i[1], params, expected_status_code, i[3])]
    return ret
