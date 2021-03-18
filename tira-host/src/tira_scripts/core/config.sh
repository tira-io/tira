#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Global config file.
#
#    Project TIRA/general
#    Author: Steve Göring
#
thisscriptpath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#
#    Define each global shared config option.
#
#    Enable or disable debug/unittest moduls, possible values: true or false.
_DEBUG=true
_UNITTEST=true
_LOG_FILE="/var/log/tira_debug.txt"

#
#    TIRA specific config section.
#
#    Note: Config variables beginning with _CONFIG_FILE_ are for files and
#        will be checked at startup.
#    Conventions:
#        Every folder constant definition does not end with /!
#

#    Tira versionstring.
_TIRA_VERSION=$(find $thisscriptpath/../ -regex ".*\(py\|sh\)" | sort | xargs cat | md5sum | awk '{print $1}')

#    TIRA username
_CONFIG_tira_username="tira"

#    TIRA groupname
_CONFIG_tira_groupname="$_CONFIG_tira_username"

#    TIRA nfs root directory.
_CONFIG_tira_nfs="/mnt/nfs/tira"

#    TIRA data directory.
_CONFIG_FILE_tira_data="$_CONFIG_tira_nfs/data"

#    TIRA log directory.
_CONFIG_FILE_tira_log="$_CONFIG_tira_nfs/log"

#    TIRA model directory.
_CONFIG_FILE_tira_model="$_CONFIG_tira_nfs/model"

#    TIRA virtual machine model directory.
_CONFIG_FILE_tira_model_virtual_machines_dir="$_CONFIG_FILE_tira_model/virtual-machines"

#    TIRA datasets model directory.
_CONFIG_FILE_tira_model_datasets_dir="$_CONFIG_FILE_tira_model/datasets"

#    TIRA task definition directory.
_CONFIG_FILE_tira_tasks_dir="$_CONFIG_FILE_tira_model/tasks"

#    TIRA state directory.
_CONFIG_FILE_tira_state="$_CONFIG_tira_nfs/state"

#    TIRA software state directory.
_CONFIG_FILE_tira_state_softwares_dir="$_CONFIG_FILE_tira_state/softwares"

#    TIRA virtual machine state directory.
_CONFIG_FILE_tira_state_virtual_machines_dir="$_CONFIG_FILE_tira_state/virtual-machines"

#    TIRA VM List.
_CONFIG_tira_vms_name="virtual-machines.txt"
_CONFIG_FILE_tira_vms="$_CONFIG_FILE_tira_model/virtual-machines/$_CONFIG_tira_vms_name"

#    TIRA VM Log.
_CONFIG_tira_vms_log_name="virtual-machine-log.txt"
_CONFIG_FILE_tira_vms_log="$_CONFIG_FILE_tira_log/virtual-machines/$_CONFIG_tira_vms_log_name"

#    TIRA HOST List.
_CONFIG_tira_hosts_name="virtual-machine-hosts.txt"
_CONFIG_FILE_tira_hosts="$_CONFIG_FILE_tira_model/virtual-machine-hosts/$_CONFIG_tira_hosts_name"

#    TIRA HOST Log.
_CONFIG_tira_hosts_log_name="virtual-machine-host-log.txt"
_CONFIG_FILE_tira_hosts_log="$_CONFIG_FILE_tira_log/virtual-machine-hosts/$_CONFIG_tira_hosts_log_name"

#    TIRA VM FOLDER
_CONFIG_FILE_tira_vm_dir="$_CONFIG_FILE_tira_data/virtual-machine-templates"

#    TIRA RUNS FOLDER
_CONFIG_FILE_tira_runs_dir="$_CONFIG_FILE_tira_data/runs"

#    TIRA USERS FOLDER
_CONFIG_FILE_tira_users_dir="$_CONFIG_FILE_tira_model/users"

#    TIRA USERS TEXT FILE
_CONFIG_FILE_tira_users_txt="$_CONFIG_FILE_tira_users_dir/users.prototext"

#    TIRA DATASETS
_CONFIG_FILE_tira_datasets_dir="$_CONFIG_FILE_tira_data/datasets"

#    TIRA TEST DATASETS NAME
_CONFIG_tira_test_datasets_name="test-datasets"

#    TIRA TEST DATASETS TRUTH NAME
_CONFIG_tira_test_datasets_truth_name="test-datasets-truth"

#    TIRA TEST DATASETS
_CONFIG_FILE_tira_test_datasets_dir="$_CONFIG_FILE_tira_datasets_dir/$_CONFIG_tira_test_datasets_name"

#    TIRA TEST DATASETS TRUTH
_CONFIG_FILE_tira_test_datasets_truth_dir="$_CONFIG_FILE_tira_datasets_dir/$_CONFIG_tira_test_datasets_truth_name"

#    TIRA TRAINING DATASETS NAME
_CONFIG_tira_training_datasets_name="training-datasets"

#    TIRA TRAINING DATASETS TRUTH NAME
_CONFIG_tira_training_datasets_truth_name="training-datasets-truth"

#    TIRA TRAINING DATASETS
_CONFIG_FILE_tira_training_datasets_dir="$_CONFIG_FILE_tira_datasets_dir/$_CONFIG_tira_training_datasets_name"

#    TIRA TRAINING DATASETS TRUTH
_CONFIG_FILE_tira_training_datasets_truth_dir="$_CONFIG_FILE_tira_datasets_dir/$_CONFIG_tira_training_datasets_truth_name"


#    User name and password of the default account in virtual machine templates
_CONFIG_tira_default_template_admin_username_windows="Administrator"
_CONFIG_tira_default_template_admin_username_fedora="Administrator"
_CONFIG_tira_default_template_admin_username_ubuntu="administrator"
_CONFIG_tira_default_template_admin_password="2012.tira"

#    Backup prefix for names.
_CONFIG_tira_backup_name_prefix="pan15"

#
#    TIRA client settings.
#

#    TIRA client home folder.
_CONFIG_FILE_tira_local_home="/home/$_CONFIG_tira_username/.tira"

#
#    TIRA local vms.txt
#
_CONFIG_tira_local_home_log_file_header="host-pc vmname=vmid-os tiraport sshport rdpport admin admin-pw user user-pw"

#
#    TIRA NFS Server settings.
#

#    TIRA NFS Server directory.
_CONFIG_tira_srv="/srv/tira"

#
#    TIRA cvs repository url
#
_CONFIG_tira_cvs_root="webis.uni-weimar.de/srv/cvsroot"
_CONFIG_tira_cvs_subdir="code-in-progress/tira"

#
#    Disraptor settings
#
_CONFIG_tira_disraptor_url="https://www.tira.io"

#
#    Export for usage in other scripts.
#
export _DEBUG
export _UNITTEST
