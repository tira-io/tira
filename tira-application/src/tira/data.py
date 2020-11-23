"""
p.stat().st_mtime - change time
"""
import TiraClientWebMessages_pb2 as modelpb
from google.protobuf.text_format import Parse
from pathlib import Path

MODEL_ROOT = Path("/mnt/ceph/tira/model")
TASKS_DIR_PATH = MODEL_ROOT / Path("tasks")
ORGANIZERS_FILE_PATH = MODEL_ROOT / Path("organizers/organizers.prototext")


class FileDatabase(object):

    def __init__(self):
        pass

    def get_task_list(self):
        """ Get a list of the tasks
        :return: a list [{name, organization, year, dataset_count, participant_count, website}]
        model/tasks/xxx.prototext - id, name, description, datasets, hostID, web
        model/organizers/organziers.prototext - id, name, years, web
        """
        # organizaer name resolution
        organizers = modelpb.Hosts()
        Parse(open(ORGANIZERS_FILE_PATH, "r").read(), organizers)
        for org in organizers.hosts:
            print("-", org)
        # get all tasks




