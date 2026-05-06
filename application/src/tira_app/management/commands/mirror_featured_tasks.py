from django.core.management.base import BaseCommand
from tira_app import model as modeldb
from tira_app.tira_model import model as db
from subprocess import check_output
from pathlib import Path

# vim /home/tira/.local/lib/python3.11/site-packages/tira_app/management/commands/mirror_featured_tasks.py
# sudo apt-get install 
# ./manage.py mirror_featured_tasks

TASKS_TO_SKIP = set(["ir-benchmarks"])

class Command(BaseCommand):
    def featured_tasks(self):
        ret = set()
        for i in modeldb.Task.objects.all():
            if not i.featured or i.task_id in TASKS_TO_SKIP:
                continue
            ret.add(i.task_id)
        
        return ret

    def rsync(self, src: str, dst: str):
        cmd = [
            "rsync",
            "-a",
            "--size-only",
            "--ignore-existing",
            f"{src.rstrip('/')}/",
            f"{dst.rstrip('/')}/"
        ]

        print(" ".join(cmd))
        check_output(cmd)

    def mirror_directory(self, directory):
        if "/mnt/ceph/tira/" not in str(directory):
            raise ValueError(f"Unexpected directory {directory}.")

        SKIP_LIST = []
        SKIP_LIST = set([i for i in SKIP_LIST] + [i + '/' for i in SKIP_LIST])
        if directory in SKIP_LIST:
            print("Skip ", directory)
            return

        ceph_fs_dir = str(directory).replace("/mnt/ceph/tira/", "/mnt/ceph/tira-ceph-fs/")
        if not Path(ceph_fs_dir).is_dir():
            return

        pvc_dir = str(directory).replace("/mnt/ceph/tira/", "/mnt/ceph/tira-pvc/")

        Path(pvc_dir).parent.mkdir(parents=True, exist_ok=True)
        print(f"Mirror between:\n\t- {ceph_fs_dir}\n\t-{pvc_dir}\n")
        self.rsync(ceph_fs_dir, pvc_dir)
        self.rsync(pvc_dir, ceph_fs_dir)

    def mirror_datasets(self, task_id):
        for i in modeldb.Dataset.objects.filter(default_task__task_id=task_id):
            dataset_type = i.dataset_id.split("-")[-1]
            # mirror inputs dir
            self.mirror_directory(db.data_path / f"{dataset_type}-datasets" / task_id / i.dataset_id)

            # mirror truths dir
            self.mirror_directory(db.data_path / f"{dataset_type}-datasets-truth" / task_id / i.dataset_id)

            # mirror run dir
            self.mirror_directory(db.runs_dir_path / i.dataset_id)

    def handle(self, *args, **options):
        tasks = self.featured_tasks()
        for task in tasks:
            self.mirror_datasets(task)

    def add_arguments(self, parser):
        pass
