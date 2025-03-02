from pathlib import Path

from tira.ir_datasets_loader import IrDatasetsLoader

IrDatasetsLoader = IrDatasetsLoader


def run_irds_command(task_id, dataset_id, image, command, output_dir, truth_command, truth_output_dir):
    from .tira_model import model
    from .util import run_cmd_as_documented_background_process

    irds_root = model.custom_irds_datasets_path / task_id / dataset_id
    command = command.replace("$outputDir", "/output-tira-tmp/")
    truth_command = truth_command.replace("$outputDir", "/output-tira-tmp/")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(truth_output_dir).mkdir(parents=True, exist_ok=True)
    Path(irds_root).mkdir(parents=True, exist_ok=True)

    command = [
        [
            "sudo",
            "podman",
            "--storage-opt",
            "mount_program=/usr/bin/fuse-overlayfs",
            "run",
            "-v",
            f"{irds_root}:/root/.ir_datasets",
            "-v",
            f"{output_dir}:/output-tira-tmp/",
            "--entrypoint",
            "sh",
            image,
            "-c",
            command,
        ],
        [
            "sudo",
            "podman",
            "--storage-opt",
            "mount_program=/usr/bin/fuse-overlayfs",
            "run",
            "-v",
            f"{irds_root}:/root/.ir_datasets",
            "-v",
            f"{truth_output_dir}:/output-tira-tmp/",
            "--entrypoint",
            "sh",
            image,
            "-c",
            truth_command,
        ],
    ]

    descriptions = ["### Import Dataset (Without Ground Truth ###", "### Import Ground Truth ###"]

    # For debug purposes
    # command = ['sh', '-c', 'ecsho "1"; sleep 2s; echo "2"; sleep 2s; echo "3"; sleep 2s; echo "4";' +
    #           'echo "5"; sleep 2s; echo "6"; sleep 2s; echo "7"; sleep 2s; echo "8";' +
    #           'echo "9"; sleep 2s; echo "10"; sleep 2s; echo "11"; sleep 2s; echo "12";' +
    #           'echo "13"; sleep 2s; echo "14"; sleep 2s; echo "15"; sleep 2s; echo "16"'
    #           ]
    # command = [command, command]

    return run_cmd_as_documented_background_process(
        cmd=command, vm_id=None, task_id=task_id, title=f"Import Dataset {dataset_id}", descriptions=descriptions
    )
