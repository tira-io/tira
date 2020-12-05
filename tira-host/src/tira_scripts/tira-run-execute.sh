#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Martin Potthast, Anna Beyer, Adrian Teschendorf, Steve Göring

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="apt-get sudo wget"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <submission-file> <input-dataset-name> <input-run-name> <outpur-dir-name> <sandboxed> [<optional-parameters>]

Description:
    Executes a participant's submission for a task. The submission is expected to
    take the input directory as a dataset

Options:
    -h | --help           Displays this help
    -r | --remote [host]  Remote control a specific host

Parameter:
    <submission-file>       Contains user credentials and the software command
    <input-dataset-name>    Name of the input directory where a task's dataset is
                            located in the shared folder inside the virtual machine.
    <input-run-path>        Path to the run to serve as additional input to the
                            software, or 'none', is no run is provided.
    <outpur-dir-name>       Name of the ouptut directory where the software is
                            supposed to store its output, or 'auto' if it shall
                            be chosen automatically.
    <sandboxed>             Flag indicating whether the virtual machine shall be
                            sandboxed before executing the software.
    <optional-parameters>   Additional task-specific parameters, such as an access
                            token for source retrieval, or language and genre tags
                            for author identification. The parameters must be
                            formatted as follows:
                                'token=my-token;language=en;genre=reviews'

Examples:
    $(basename "$0") 'submission-text-alignment.txt' 'pan14-text-alignment-mini-dataset' true
    $(basename "$0") 'submission-source-retrieval.txt' 'pan14-source-retrieval-mini-dataset' false

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
#    Creates a TIRA host on a local machine or via remote control.
#
main() {
    logCall "$(basename "$0") $@"
    # Check number of parameters.
    if [ "$#" -ne 5 ] && [ "$#" -ne 6 ]; then
        logError "Wrong amount of parameters: $# but expected 5 or 6, see:"
        usage
    fi

    submissionFileDir="$_CONFIG_FILE_tira_state_softwares_dir"
    runDir="$_CONFIG_FILE_tira_runs_dir"
    timestamp=$(date +%F-%H-%M-%S)

    submissionFileName="$1"
    inputDatasetName="$2"
    inputRunPath="$3"
    outputDirName="$4"
    sandboxed="$5"

    taskname="${FLAGS_taskname}"
    logInfo "Task: $taskname"

    # Check for additional parameters.
    if [ "$#" -eq 6 ]; then
        additonalParameters="$6"
        # Evaluate additional Parameters.
        # TODO: Using eval is an anti-pattern. Is there a better way?
        eval "$additonalParameters"
    fi

    # Define inputDataset.
    # TODO: Remove the construct of submission files altogether."
    submissionFile=$(find "$submissionFileDir" -type f -name "$submissionFileName")
    if [ ! -e "$submissionFile" ]; then
        logError "$submissionFileName does not exist, check path: $submissionFile."
        usage
    fi
    # Source submission file to populate its variables (e.g., $user, $host, etc.)
    . "$submissionFile"

    # Define access token for data server access.
    runPrototext="$runDir/$inputDatasetName/$user/$outputDirName/run.prototext"
    accessToken=$(get_access_token_from_tira_run_definition "$runPrototext")
    # NOTE. The variable is picked up via the submission files sourced later.
    export accessToken

    # TODO: For legacy reasons, i.e., the source retrieval task softwares.
    # Can be fixed by changing the corresponding commands and adding the access
    # token variable to the corresponding runs.
    if [ "$outputDirName" = "auto" ]; then
        token="$user-$timestamp"
    else
        token="$user-$outputDirName"
    fi
    # NOTE. The variable is picked up via the submission files sourced later.
    export token

    # Define shared folder, and output directory according os.
    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
        if [[ "$inputDatasetName" == *"test"* ]]; then
            sharedFolder="/media/$_CONFIG_tira_test_datasets_name"
            sharedFolderName="$_CONFIG_tira_test_datasets_name"
            datasetsDir="$_CONFIG_FILE_tira_test_datasets_dir"
        else
            sharedFolder="/media/$_CONFIG_tira_training_datasets_name"
            sharedFolderName="$_CONFIG_tira_training_datasets_name"
            datasetsDir="$_CONFIG_FILE_tira_training_datasets_dir"
        fi
        if [ "$outputDirName" = "auto" ]; then
            outputRunDir="/tmp/$user/$timestamp"
        else
            outputRunDir="/tmp/$user/$outputDirName"
        fi
    elif [ "$os" = "windows" ]; then
        if [[ "$inputDatasetName" == *"test"* ]]; then
            sharedFolder="//VBOXSVR/$_CONFIG_tira_test_datasets_name"
            sharedFolderName="$_CONFIG_tira_test_datasets_name"
            datasetsDir="$_CONFIG_FILE_tira_test_datasets_dir"
        else
            sharedFolder="//VBOXSVR/$_CONFIG_tira_training_datasets_name"
            sharedFolderName="$_CONFIG_tira_training_datasets_name"
            datasetsDir="$_CONFIG_FILE_tira_training_datasets_dir"
        fi
        # The path must be Windows style, or else the software won't find it
        if [ "$outputDirName" = "auto" ]; then
            outputRunDir="C:/Windows/Temp/$user/$timestamp"
        else
            outputRunDir="C:/Windows/Temp/$user/$outputDirName"
        fi
    fi

    inputDataset="$sharedFolder/$taskname/$inputDatasetName"
    outputDir="$outputRunDir/output"
    
    # Retrieve data server, if any, from dataset model
    if [[ "$inputDatasetName" == *"test"* ]]; then
        datasetPrototex="$_CONFIG_FILE_tira_model_datasets_dir/$taskname/$inputDatasetName.prototext"
    else
        datasetPrototex="$_CONFIG_FILE_tira_model_datasets_dir/$taskname/$inputDatasetName.prototext"
    fi
    dataServer=$(get_data_server_from_tira_dataset_definition "$datasetPrototex")

    logInfo "Input dataset: $inputDataset"
    logInfo "Output dir: $outputDir"
    logInfo "Data server: $dataServer"

    # Define input run directory.
    if [ "$inputRunPath" != "none" ]; then
        if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
            inputRun="/tmp/inputRun"
        elif [ "$os" = "windows" ]; then
           # The path must be Windows style, or else the software won't find it
            inputRun="C:/Windows/Temp/inputRun"
        fi
        logInfo "$user@$host: input run $inputRunPath to be found at $inputRun"
    else
        inputRun="none"
    fi

    # Include user specific data again for correct binding of command line parameters.
    . "$submissionFile"

    # Get hostname (webisxx) for remote sandboxing/unsandboxing.
    hostname=$(echo "$host" | cut -d'.' -f 1)
    logTodo "webis specific code"
    if [ "$hostname" != "webis*" ]; then
        hostname="localhost"
    fi
    
    # Sandbox VM if requested.
    if [ "$sandboxed" = "true" ]; then

        logInfo "Sandboxing virtual machine..."
        
        vm_info=$(get_vm_info_from_tira "$user")
        vmname=$(echo "$vm_info" | grep "vmName" | sed "s|vmName=||g")

        if [[ "$inputDataset" == *"test"* ]]; then
            mountTestData=true
        else
            mountTestData=false
        fi

        if [ "$taskname" != "" ]; then
            tira_call vm-sandbox -r "$hostname" "$vmname" "$outputDirName" "$mountTestData" -T "$taskname"
        else
            tira_call vm-sandbox -r "$hostname" "$vmname" "$outputDirName" "$mountTestData"
        fi

        #host="localhost"  # because in sandboxed mode vm is just rechable via localhost

        # get stored sandbox config
        logDebug "try to get sandbox info file: $_CONFIG_FILE_tira_state_virtual_machines_dir/~$vmname.sandboxed"
        if [ ! -f "$_CONFIG_FILE_tira_state_virtual_machines_dir/~$vmname.sandboxed" ]; then
            logError "There is something wrong with sandboxing, $_CONFIG_FILE_tira_state_virtual_machines_dir/~$vmname.sandboxed does not exist!"
        fi
        . "$_CONFIG_FILE_tira_state_virtual_machines_dir/~$vmname.sandboxed"

        sshport="$natsshport"
        logDebug "set sshport to : $natsshport"
    fi

    # Loop while connection can be established.
    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o ConnectTimeout=10 \
        -o ConnectionAttempts=100 \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "exit"


    # Mount transient shared folder in ubuntu vms, since they are not mounted automatically withouth restart.
#    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
#        if [[ "$inputDatasetName" == *"test"* ]]; then
#            logInfo "$user@$host: creating shared folder $sharedFolder"
#            #sshpass -p "$userpw" ssh "$user@$host" -p "$sshport"\
#            #    -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
#            #    -o LogLevel=error -t -t "echo $userpw| sudo -S mkdir $sharedFolder; exit"
#            logDebug "Don't mount anything, because sandbox script mounts all needed directories."
#            #sshpass -p "$userpw" ssh "$user@$host" -p "$sshport"\
#            #    -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
#            #    -o LogLevel=error -t -t "echo $userpw | sudo -S mount -t vboxsf $sharedFolderName $sharedFolder; exit"
#        fi
#    fi

    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o ConnectTimeout=10 \
        -o ConnectionAttempts=100 \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "cd $inputDataset; exit"

    # Copy the input run into the virtual machine into the tmp folder.
    if [ "$inputRunPath" != "none" ]; then
        logInfo "$user@$host: copying input run into the virtual machine..."
        sshpass -p "$userpw" \
          scp \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o LogLevel=error \
            -r \
            -P "$sshport" "$inputRunPath/output" "$user@$host:$inputRun"
    fi

    # Handle empty cmd.
    if [ "$cmd" = "" ]; then
        cmd=":"
    fi

    # Define timedCmd.
    if [ "$os" = "ubuntu" ] || [ "$os" = "fedora" ]; then
        timedCmd="(echo -e '$cmd\n\n' && /usr/bin/time -o $outputRunDir/runtime.txt $cmd) 1> $outputRunDir/stdout.txt 2> $outputRunDir/stderr.txt"
    elif [ "$os" = "windows" ]; then
        timedCmd="{ time { echo -e '$cmd\n\n' && $cmd ; } 1> $outputRunDir/stdout.txt 2> $outputRunDir/stderr.txt ; } 2> $outputRunDir/runtime.txt"
    fi

    # Execute program on vm.
    logTodo "How can we avoid keeping an ssh connection open during executing a software in a VM?"

    logInfo "$user@$host: establishing SSH connection and executing command..."
    logInfo "\t$cmd"
    # This SSH connection can last for a very long time, so that a keep alive signal is necessary.
    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o TCPKeepAlive=yes \
        -o ServerAliveInterval=60 \
        -o LogLevel=error \
        -t \
        -t "mkdir -p $outputDir; cd $workingDir; if [ -f ~/.bashrc ]; then source ~/.bashrc; fi; $timedCmd; exit"

    # Bugfix for the subsequent scp command: http://stackoverflow.com/questions/12440287/scp-doesnt-work-when-echo-in-bashrc
    # The proposed solutions all solve the problem within .bashrc, but we cannot
    # rely on users acting this way. This we go the brute force path and delete
    # the .bashrc before copying. We may do this, since the VM has been cloned
    # and the clone will be deleted, anyway.
    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "rm ~/.bashrc"
    # Copy outputDir from vm to localhost.
    logInfo "$user@$host: copying $outputDir from VM..."
    localRunDir="$runDir/$inputDatasetName/$user"
    mkdir -p "$localRunDir"
    sshpass -p "$userpw" \
      scp \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -r \
        -P "$sshport" "$user@$host:$outputRunDir" "$localRunDir"

    # Reset access rights.
    chmod -R 775 "$localRunDir/$outputDirName"

    # Remove outputDir on vm.
    logInfo "$user@$host: removing $outputDir from VM..."
    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "rm -rf $outputRunDir; exit"

    # Remove inputRun on vm.
    logInfo "$user@$host: removing $outputDir from VM..."
    sshpass -p "$userpw" \
      ssh "$user@$host" \
        -p "$sshport" \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no \
        -o LogLevel=error \
        -t \
        -t "rm -rf $inputRun; exit"

    # Determine size of the run.
    logInfo "executing command: (du -sb $localRunDir/$outputDirName && du -hs $localRunDir/$outputDirName) | cut -f1 > $localRunDir/$outputDirName/size.txt"
    (du -sb "$localRunDir/$outputDirName" && du -hs "$localRunDir/$outputDirName") | cut -f1 > "$localRunDir/$outputDirName/size.txt"
    # Count lines.
    find "$localRunDir/$outputDirName/output" -type f -exec cat {} + | wc -l | tee -a "$localRunDir/$outputDirName/size.txt" >/dev/null
    # Count files.
    find "$localRunDir/$outputDirName/output" -type f | wc -l >> "$localRunDir/$outputDirName/size.txt"
    # Count directories.
    find "$localRunDir/$outputDirName/output" -type d | wc -l >> "$localRunDir/$outputDirName/size.txt"

    # Create file listing.
    tree -ahv "$localRunDir/$outputDirName/output" > "$localRunDir/$outputDirName/file-list.txt"

    # Runs must be readable and writable by the tira user and the tira group.
    chmod -R ug+rw "$localRunDir/$outputDirName"
    chmod ug+rw "$localRunDir"

    # Get VM out of sandbox, if necessary.
    if [ "$sandboxed" = "true" ]; then
        logInfo "unsandboxing virtual machine..."
        tira_call vm-unsandbox -r "$hostname" "$vmname"
    fi
    logInfo "$user@$host: done."
}

#
#    Start programm with parameters.
#
main "$@"
