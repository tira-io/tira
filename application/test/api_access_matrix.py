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
        url_pattern="api/snippets-for-tirex-components",
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
        url_pattern="api/v1/anonymous-uploads/<str:dataset_id>",
        params={"dataset_id": 1},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,
        },
    ),
    route_to_test(
        url_pattern="api/v1/anonymous-uploads/<str:dataset_id>",
        params={"dataset_id": "does-not-exist"},
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
        url_pattern="tira-admin/export-participants/<str:task_id>.csv",
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
        url_pattern="tira-admin/export-participants/<str:task_id>.csv",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/vm",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/add_software/vm",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/save_software/vm/<str:software_id>",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/vm/<str:software_id>",
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
        params={
            "task_id": "shared-task-1",
            "vm_id": "example_participant",
            "software_id": 0,
            "docker_software_id": "<str:docker_software_id>",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>",
        params={
            "task_id": "shared-task-1",
            "vm_id": PARTICIPANT.split("_")[-1],
            "software_id": 0,
            "docker_software_id": "<str:docker_software_id>",
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
        url_pattern="task/<str:task_id>/vm/<str:vm_id>/delete_software/docker/<str:docker_software_id>",
        params={
            "task_id": "task-of-organizer-1",
            "vm_id": "example_participant",
            "software_id": 0,
            "docker_software_id": "<str:docker_software_id>",
        },
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
        url_pattern="grpc/<str:vm_id>/vm_info",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_info',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/vm_state",
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
        url_pattern="grpc/<str:vm_id>/vm_state",
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
        url_pattern="grpc/<str:vm_id>/vm_start",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_start',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/vm_shutdown",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_shutdown',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/vm_stop",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_stop',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/run_abort",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/run_abort',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
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
        url_pattern="grpc/<str:vm_id>/vm_running_evaluations",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,
        },
    ),
    # Skip for the moment, takes too long. Maybe mock later?
    # route_to_test(
    #    url_pattern='grpc/<str:vm_id>/vm_running_evaluations',
    #    params={'vm_id': PARTICIPANT.split('_')[-1]},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="grpc/<str:vm_id>/get_running_evaluations",
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
        url_pattern="grpc/<str:vm_id>/get_running_evaluations",
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
        url_pattern="grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>",
        params={"task_id": "shared-task-1", "vm_id": "does-not-exist", "software_id": "does-not-exist"},
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
    #    url_pattern='grpc/<str:task_id>/<str:vm_id>/run_execute/vm/<str:software_id>',
    #    params={'task_id': 'shared-task-1', 'vm_id': PARTICIPANT.split('_')[-1], 'software_id': f'software-of-{PARTICIPANT.split("_")[-1]}'},
    #    group_to_expected_status_code={
    #        ADMIN: 200,
    #        GUEST: 302,
    #        PARTICIPANT: 200,
    #        ORGANIZER: 302,
    #    },
    # ),
    route_to_test(
        url_pattern="grpc/<str:task_id>/<str:vm_id>/run_execute/docker/<str:dataset_id>/<str:docker_software_id>/<str:docker_resources>/<str:rerank_dataset>",
        params={
            "task_id": "shared-task-1",
            "vm_id": "does-not-exist",
            "dataset_id": "does-not-exist",
            "docker_software_id": "does-not-exist",
            "rerank_dataset": "none",
            "docker_resources": "<str:docker_resources>",
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
            "docker_resources": "<str:docker_resources>",
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
        url_pattern="tira-admin/reload/vms",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/reload/datasets",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/reload/tasks",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/create-vm",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/modify-vm",
        params={},
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
        url_pattern="tira-admin/import-irds-dataset/<str:task_id>",
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
        url_pattern="tira-admin/import-irds-dataset/<str:task_id>",
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
        url_pattern="tira-admin/add-organizer/<str:organizer_id>",
        params={"organizer_id": "organizer-2"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,  # We expect 405 for existing organizer 'organizer-2'
            PARTICIPANT: 405,  # We expect 405 for existing organizer 'organizer-2'
            ORGANIZER: 405,  # We expect 405 for existing organizer 'organizer-2'
            ORGANIZER_WRONG_TASK: 405,  # We expect 405 for existing 'organizer-2'
        },
    ),
    route_to_test(
        url_pattern="tira-admin/add-organizer/<str:organizer_id>",
        params={"organizer_id": "organizer-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 200,
            PARTICIPANT: 200,  # We expect 200 for non-existing organizer.
            ORGANIZER: 200,  # We expect 200 for non-existing organizer.
            ORGANIZER_WRONG_TASK: 200,  # We expect 200 for non-existing organizer.
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-organizer/<str:organizer_id>",
        params={"organizer_id": "organizer-id-does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-organizer/<str:organizer_id>",
        params={"organizer_id": "organizer-2"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="tira-admin/edit-organizer/<str:organizer_id>",
        params={"organizer_id": "EXAMPLE-ORGANIZER"},
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
        url_pattern="tira-admin/create-group/<str:vm_id>",
        params={"vm_id": "vm-id-does-not-exist"},
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
            GUEST: 200,  # TODO Make consistent with "api/evaluation/<str:vm_id>/<str:run_id>"
            PARTICIPANT: 200,
            ORGANIZER: 200,
            ORGANIZER_WRONG_TASK: 200,  # TODO Make consistent with "api/evaluation/<str:vm_id>/<str:run_id>"
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
        url_pattern="api/evaluation/<str:vm_id>/<str:run_id>",
        params={"vm_id": "example-participant", "run_id": "run-1-example_participant"},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
            PARTICIPANT: 302,
            ORGANIZER: 302,
            ORGANIZER_WRONG_TASK: 302,  # TODO Make consistent with "api/evaluations/<str:task_id>/<str:dataset_id>"
        },
    ),
    route_to_test(
        url_pattern="api/evaluation/<str:vm_id>/<str:run_id>",
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
        url_pattern="api/ova-list",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/host-list",
        params={},
        group_to_expected_status_code={
            ADMIN: 200,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
    ),
    route_to_test(
        url_pattern="api/organizer-list",
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
        url_pattern="api/organizer/<str:organizer_id>",
        params={"organizer_id": "organizer-id-id-does-not-exist"},
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
    # TODO: The following methods return 50X at the moment, we should improve the setup so that it returns 200. But for the moment 50X is enough to separate authenticated from unauthenticated.
    route_to_test(
        url_pattern="tira-admin/reload-data",
        params={},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
        hide_stdout=True,
    ),
    route_to_test(
        url_pattern="tira-admin/reload-runs/<str:vm_id>",
        params={"vm_id": "does-not-exist"},
        group_to_expected_status_code={
            ADMIN: 500,
            GUEST: 405,
            PARTICIPANT: 405,
            ORGANIZER: 405,
            ORGANIZER_WRONG_TASK: 405,
        },
        hide_stdout=True,
    ),
    route_to_test(
        url_pattern="tira-admin/archive-vm",
        params={},
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
    route_to_test(
        url_pattern="health",
        params={},
        group_to_expected_status_code={
            GUEST: 204,
            PARTICIPANT: 204,
            ORGANIZER_WRONG_TASK: 204,
            ORGANIZER: 204,
            ADMIN: 204,
        },
    ),
    route_to_test(
        url_pattern="info",
        params={},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/datasets/",
        params={},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/datasets/all",
        params={},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern=".well-known/tira/client",
        params={},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/systems/",
        params={},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/systems/<str:user_id>/<str:software>",
        params={"user_id": "does-not-exist", "software": "does-not-exist"},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
    # The following v1/ endpoints should be restricted to only allow admin-access for now
    route_to_test(
        url_pattern="v1/evaluations/",
        params={},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/organizers/",
        params={},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/organizers/",
        params={},
        method="POST",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            # ADMIN: 200,  # TODO: replace with correct code once the POST is properly implemented
        },
    ),
    route_to_test(
        url_pattern="v1/organizers/<str:organizer_id>/",
        params={"organizer_id": "does-not-exist"},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/organizers/<str:organizer_id>/",
        params={"organizer_id": "does-not-exist"},
        method="DELETE",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/runs/",
        params={},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/runs/<str:run_id>/",
        params={"run_id": "does-not-exist"},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/runs/<str:run_id>/",
        params={"run_id": "does-not-exist"},
        method="DELETE",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/runs/<str:run>/review",
        params={"run": "does-not-exist"},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/",
        params={},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/",
        params={},
        method="POST",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            # ADMIN: 200,  # TODO: replace with correct code once the POST is properly implemented
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/<str:task_id>/",
        params={"task_id": "does-not-exist"},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/<str:task_id>/",
        params={"task_id": "does-not-exist"},
        method="DELETE",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            ADMIN: 404,
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/<str:task_id>/evaluations",
        params={"task_id": "does-not-exist"},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            # ADMIN: 404,  # FIXME: this does not currently work
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/<str:task_id>/registrations",
        params={"task_id": "does-not-exist"},
        method="GET",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            # ADMIN: 404,  # FIXME: this does not currently work
            ADMIN: 200,
        },
    ),
    route_to_test(
        url_pattern="v1/tasks/<str:task_id>/registrations",
        params={"task_id": "does-not-exist"},
        method="POST",
        group_to_expected_status_code={
            GUEST: 403,
            PARTICIPANT: 403,
            ORGANIZER_WRONG_TASK: 403,
            ORGANIZER: 403,
            # ADMIN: 404,  # TODO: these should give 404 for non-existant tasks. That is not currently the case
        },
    ),
    route_to_test(
        url_pattern="v1/user/",
        params={},
        group_to_expected_status_code={
            GUEST: 200,
            PARTICIPANT: 200,
            ORGANIZER_WRONG_TASK: 200,
            ORGANIZER: 200,
            ADMIN: 200,
        },
    ),
]


def access_matrix_for_user(user: str) -> list[tuple]:
    ret = []
    for i in API_ACCESS_MATRIX:
        if user not in i[2]:
            continue
        params = i[2][user]["params"]
        expected_status_code = i[2][user]["expected_status_code"]

        ret += [(i[0], i[1], params, expected_status_code, i[3])]
    return ret
