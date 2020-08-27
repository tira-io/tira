#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Anna Beyer, Adrian Teschendorf, Steve Göring
#

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage(){
    logTodo "parameter are not matching description."
    echo "
Usage:
    $(basename "$0") [flags] <submission-file> <truth-dir> <run-dir>

Description:
    Evaluates a submission run on the master VM. It produces another folder named
    <run-directory-name>-eval containing the evaluation run output as well as
    stdout and stderr.

Options:
    -h | --help             Displays this help
    -r | --remote [host]    Remote control a specific host

Parameter:
    <submission-file>       Absolute path to the evaluation software submission file.
                            It contains master VM credentials and the task specific
                            evaluation software command
    <input-dataset-name>    Name of the evaluation dataset.
    <input-run>             Absolute path to the input directory where a user's
                            software run is located.
    <outpur-dir-name>       Name of the ouptut directory where the software is
                            supposed to store its output, or 'auto' if it shall
                            be chosen automatically.

Examples:
    $(basename "$0") 'submission-eval-text-alignment.txt' 'pan13-text-alignment-training-dataset-2013-01-21' 'pan13-text-alignment-training-dataset-2013-01-21/rodrigueztorrejon14/2014-04-02-19-07-58'

Authors:
    Martin Potthast
    Anna Beyer
    Adrian Teschendorf
    Steve Göring"
    exit 1
}

#
#    Define command line arguments and parse them.
#
DEFINE_string taskname "" 'taskname' 'T'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Executes a participant's submission for a task. The submission is expected to
#    take the input directory as a dataset
#
main() {

    # Check number of parameters.
    if [ "$#" -ne 4 ]; then
        logError "Wrong amount of parameters, see:"
        usage
    fi

    sleep 5

    # Static variables.
    submissionFileDir="$_CONFIG_FILE_tira_state_softwares_dir"

    submissionFileName="$1"
    inputDatasetName="$2"
    localInputRun="$3"
    outputDirName="$4"

    taskname="${FLAGS_taskname}"
    logInfo "taskname: $taskname"

    # Define inputDataset.
    submissionFile=$(find "$submissionFileDir" -type f -name "$submissionFileName")

    logDebug "Submission file name: $submissionFileName"
    logDebug "Submission file dir: $submissionFileDir"
    logDebug "Submission file: $submissionFile"

    # Check if submission file exists.
    if [ ! -e "$submissionFile" ]; then
        logError "$submissionFile does not exist."
        usage
    fi

    # Include user specific data.
    . "$submissionFile"

    # Define access token for data server access.
    runPrototext="$localInputRun/run.prototext"
    accessToken=$(get_access_token_from_tira_run_definition "$runPrototext")
    # NOTE. The variable is picked up via the submission files sourced later.
    export accessToken

    inputRunName=$(echo "$localInputRun" | awk -F"/" '{print $(NF-1)"-"$NF}')

    # TODO: For legacy reasons, i.e., the source retrieval task softwares.
    # Can be fixed by changing the corresponding commands and adding the access
    # token variable to the corresponding runs.
    token="$inputRunName"

    # Define timer, shared folder, and output directory according os.
    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
        if [[ "$inputDatasetName" == *"test"* ]]; then
            sharedFolder="/media/$_CONFIG_tira_test_datasets_truth_name"
            datasetsDir="$_CONFIG_FILE_tira_test_datasets_dir"
        else
            sharedFolder="/media/$_CONFIG_tira_training_datasets_truth_name"
            datasetsDir="$_CONFIG_FILE_tira_training_datasets_dir"
        fi
    elif [ "$os" = "windows" ]; then
        if [[ "$inputDatasetName" == *"test"* ]]; then
            sharedFolder="//VBOXSVR/$_CONFIG_tira_test_datasets_truth_name"
            datasetsDir="$_CONFIG_FILE_tira_test_datasets_dir"
        else
            sharedFolder="//VBOXSVR/$_CONFIG_tira_training_datasets_truth_name"
            datasetsDir="$_CONFIG_FILE_tira_training_datasets_dir"
        fi
    fi

    # Define input dataset directory.
    inputDataset="$sharedFolder/$taskname/$inputDatasetName"

    # Define inputRun.
    inputRun="/tmp/$inputRunName/output"

    if [ "$outputDirName" = "auto" ]; then
        timestamp=$(date +%F-%H-%M-%S)
        outputRunDir="/tmp/$timestamp"
    else
        outputRunDir="/tmp/$outputDirName"
    fi
    outputDir="$outputRunDir/output"

    # Include user specific data again to fill in missing variables.
    . "$submissionFile"

    # Copy the input run into the virtual machine into the tmp folder.
    logInfo "$user@$host: copying input run into the virtual machine..."
    sshpass -p "$userpw" scp -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no -o LogLevel=error -r \
        -P "$sshport" "$localInputRun" "$user@$host:/tmp/$inputRunName"

    # Handle empty cmd.
    if [ "$cmd" = "" ]; then
        cmd=":"
    fi

    # Define timedCmd.
    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
        timedCmd="(echo -e '$cmd\n\n' && /usr/bin/time -o $outputRunDir/runtime.txt $cmd) 1> $outputRunDir/stdout.txt 2> $outputRunDir/stderr.txt"
    elif [ "$os" = "windows" ]; then
        timedCmd="{ time bash -c \"(echo -e '$cmd\n\n' && $cmd) 1> $outputRunDir/stdout.txt 2> $outputRunDir/stderr.txt\" ; } 2> $outputRunDir/runtime.txt"
    fi

    # Execute program on vm.
    logInfo "$user@$host: establishing SSH connection and executing command..."
    logInfo "\t$cmd"
    sshpass -p "$userpw" ssh "$user@$host" -p "$sshport" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
        -o LogLevel=error -t \
        -t "mkdir -p $outputDir;\
            cd $workingDir;\
            if [ -f ~/.bashrc ]; then source ~/.bashrc; fi;\
            $timedCmd;\
            exit"

    # Copy outputDir from vm to localhost.
    logInfo "$user@$host: copying $outputRunDir from VM..."
    sshpass -p "$userpw" scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=error \
        -r -P "$sshport" "$user@$host:$outputRunDir" "$localInputRun/../"

    # Remove outputDir on vm.
    logInfo "$user@$host: removing $outputDir from VM..."
    sshpass -p "$userpw" ssh "$user@$host" -p "$sshport" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
        -o LogLevel=error -t -t "rm -rf $outputRunDir; exit"

    # Remove inputRun on vm.
    logInfo "$user@$host: removing /tmp/$inputRunName from VM..."
    sshpass -p "$userpw" ssh "$user@$host" -p "$sshport" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
        -o LogLevel=error -t -t "rm -rf /tmp/$inputRunName; exit"

    # Determine size of the run.
    (du -sb "$localInputRun/../$outputDirName" && du -hs "$localInputRun/../$outputDirName") | cut -f1 > "$localInputRun/../$outputDirName/size.txt"
    # Count lines.
    find "$localInputRun/../$outputDirName/output" -type f -exec cat {} + | wc -l  | tee -a "$localInputRun/../$outputDirName/size.txt" >/dev/null
    # Count files.
    find "$localInputRun/../$outputDirName/output" -type f | wc -l >> "$localInputRun/../$outputDirName/size.txt"
    # Count directories.
    find "$localInputRun/../$outputDirName/output" -type d | wc -l >> "$localInputRun/../$outputDirName/size.txt"

    # Create file listing
    tree -ahv "$localInputRun/../$outputDirName/output" > "$localInputRun/../$outputDirName/file-list.txt"

    # Runs must be readable and writable by the tira user and the tira group.
    chmod -R ug+rw "$localInputRun/../$outputDirName"
    chmod ug+rw "$localInputRun/.."

    logInfo "$user@$host: done."
}

#
#    Start programm with parameters.
#
main "$@"
