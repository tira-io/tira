#!/usr/bin/env python

from datetime import datetime
from functools import wraps
import logging
import logging.config
import subprocess

logger = logging.getLogger(__name__)


class VMManage:
    def __init__(self, logfile=None):
        self.logfile = logfile

    def _run_tira_script(self, script_name, *args):
        """

        :param script_name: name of the tira command
        :param args: list of arguments for tira command
        :param output: if defined, output of the command is assigned to it for further parsing
        :return:
        """
        logger.debug("Start " + script_name + " command.")
        shell_command = "tira " + script_name + " " + " ".join([a for a in args])
        p = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = p.communicate()
        output = out.decode('utf-8')
        if self.logfile:
            with open(self.logfile, "a") as f:
                f.write(output)

        if p.returncode != 0:
            logger.error(f"{script_name} command finished with error: \n" + output)
            # raise subprocess.CalledProcessError(p.returncode, shell_command, output=out, stderr=err)

        return p.returncode, output

    # def checks(wrapped_function):
    #     @wraps(wrapped_function)
    #     def new_function(*args, **kwargs):
    #         """
    #         1. vm exist
    #         2. called command aligns with current vm status
    #             - vm-create only if not existing
    #             - vm-start only if stopped
    #             - vm-stop only if running
    #             - vm-delete only if existing
    #             - vm-sandbox
    #
    #         :param args:
    #         :param kwargs:
    #         :return:
    #         """
    #         wrapped_function(*args, **kwargs)
    #
    #     return new_function

    def check_vm_status(self):
        pass

    def vm_backup(self, vm_name):
        """
        - check if vm is registered
        - check if sandboxed, unsandbox
        - stop vm
        - vboxmanage export

        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-backup", vm_name)

    def vm_create(self, ova_file, vm_name):
        """
        - check if doesn't exist
        :param ova_file:
        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-create", ova_file, vm_name)

    def vm_delete(self, vm_name):
        """
        - check if existing
        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-delete", vm_name)

    def vm_info(self, vm_name):
        return self._run_tira_script("vm-info", vm_name)

    def vm_list(self):
        """
        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-list")

    def vm_sandbox(self, vm_name, output_dir_name, mount_test_data):
        """
        :param output_dir_name: timestamp format '2021-09-29-12-50-02'
        :param mount_test_data:
        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-sandbox", vm_name, output_dir_name, mount_test_data)

    def vm_shutdown(self, vm_name):
        """

        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-shutdown", vm_name)

    def vm_snapshot(self, vm_name):
        """

        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-snapshot", vm_name,
                                     f"{vm_name}-{datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ')}")

    def vm_start(self, vm_name):
        """
        - check if stopped
        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-start", vm_name)

    def vm_stop(self, vm_name):
        """
        - check if running
        # VBoxManage controlvm "$vmname" poweroff
        :param vm_name:
        :return:
        """
        return self._run_tira_script("vm-stop", vm_name)

    def vm_unsandbox(self, vm_name):
        return self._run_tira_script("vm-unsandbox", vm_name)

    def run_execute(self, vm_file, input_dataset_name, input_run_path, output_dir_name, sandboxed,
                    optional_parameters=""):
        """

        :param vm_file: 
        :param input_dataset_name: 
        :param input_run_path: 
        :param output_dir_name:
        :param sandboxed: 
        :param optional_parameters: 
        :return: 
        """
        return self._run_tira_script("run-execute-new", vm_file, input_dataset_name, input_run_path,
                                     output_dir_name,
                                     sandboxed, optional_parameters)

    def run_eval(self, vm_file, input_dataset_name, input_run_path, output_dir_name):
        """

        :param vm_file:
        :param input_dataset_name:
        :param input_run_path:
        :param output_dir_name:
        :return:
        """
        return self._run_tira_script("run-execute-new", vm_file, input_dataset_name, input_run_path, output_dir_name)
