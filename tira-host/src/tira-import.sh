#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Steve Göring, Martin Potthast
#

#""
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/core/vboxhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="VBoxManage"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags] <ovalistfile>

Description:
    Imports a tira VMs from a list of ova files

Parameters:
    <ovalistfile>          List of OVA filenames

Examples:
    $(basename "$0") my_vm (local)
    $(basename "$0") -r webis46 my_vm (remote)

Authors:
    Steve Göring, Martin Potthast"
    exit 1
}

#
#    Define command line arguments and parse them.
#
FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

get_username() {
    python - <<END
param = "$@"
print("-".join(param.split("-")[1:-6]))
END
}

# TODO: Copy from tira-configure-vm.py
get_host_id() {
    python - <<END
import socket
name = socket.gethostname()
if name.startswith("webis"):
    print(name[5:])
else:
    print("0")
END
}

get_host_name() {
    python - <<END
import socket
name = socket.gethostname()
if name.startswith("webis"):
    print(name + "medien.uni-weimar.de")
else:
    print(name)
END
}

# TODO: Copy from tira-configure-vm.py
assign_id() {
    python - <<END
import os

DEFAULT_PORT_SSH = 44400
DEFAULT_PORT_RDP = 55500
VM_OVERVIEW = "$_CONFIG_FILE_tira_local_home/vms.txt"
VM_OVERVIEW_HEADER = "host-pc vmname=vmid-os tiraport sshport rdpport " \
    "admin admin-pw user user-pw"
SEPARATOR = "-" * 79

def assign_id():
    """ Assign ID to vm. """
    vmid = 1
    if os.path.isfile(VM_OVERVIEW):
        vms = [x.rstrip() for x in file(VM_OVERVIEW).readlines() if x.rstrip() != SEPARATOR]
        vms.pop(0)  # remove header

        vm_ids = set()
        for vm in vms:
            host_pc, vm_name, vm_ip, vm_sshport, vm_rdpport, \
                admin_name, admin_pw, user_name, user_pw, = vm.split(' ')

            vm_id = int(vm_sshport) - DEFAULT_PORT_SSH
            vm_ids.add(int(vm_id))
        overview = open(VM_OVERVIEW, 'r')
        if len(vm_ids) > 0:
            allowed_ids = set(range(1, 51)) # TODO: Lift the limit of 50 VMs per machine.
            missing_ids = sorted(list(allowed_ids - set(vm_ids)))
            if len(missing_ids) > 0:
               vmid = missing_ids[0]
            else:
               return 51
    else:
        overview = open(VM_OVERVIEW, 'w')
        header = VM_OVERVIEW_HEADER + '\n'
        overview.write(header)
        overview.flush()
    overview.close()
    return vmid


print(str(assign_id()))
END
}

#
#    modify configuration entry in nfs.
#
patch_entry() {
    python - <<END

def build_prototext(values, key="users"):
    """
    convert dictionary to prototext format
    :key each entry starts with this key
    """
    res = ""
    for k in values:
        res += """{}: "{}"\n""".format(k, values[k])

    return res


def read_prototext(filename):
    """
    read a "text"-prototext file to a dictionary structure
    :filename filename of prototext file
    :return dictionary of all stored values
    """
    f = open(filename, "r")
    curr_values = {}
    for l in f:
        l = l.strip()

        tmp = l.split(":")
        if len(tmp) == 2:
            curr_values[tmp[0].replace("\"","").strip()] = tmp[1].replace("\"","").strip()

    f.close()
    return curr_values

username, hostname, portSsh, portRdp, vmId, ip, vmName = "$@".split(" ")

conffile = "$_CONFIG_FILE_tira_model_virtual_machines_dir/" + username + ".prototext"

values = read_prototext(conffile)

values["host"] = hostname
if "hostname" in values:
    del values["hostname"]
values["portSsh"] = portSsh
values["portRdp"] = portRdp
values["vmId"] = vmId
values["ip"] = ip
values["vmName"] = vmName

f = open(conffile, "w")
f.write(build_prototext(values))
f.close()
END
}

#
#    Imports vms from an ova file.
#
main() {

    # Print usage screen if wrong parameter count.
    if [ "$#" -eq 0 ]; then
        logError "Missing arguments see:"
        usage
    fi

    ovalist="$1"
    if [ ! -f "$ovalist" ]; then
        logError "$ovalist is not a valid file."
        exit 1
    fi

    # Process list entry.
    while read ovafile; do
        if [ "$ovafile" != "" ]; then
            username=$(get_username "$(basename $ovafile)")
            vm_info=$(get_vm_info_from_tira "$username")
            oldvmid=$(echo "$vm_info" | grep "vmId=" | sed "s|vmId=||g")
            oldvmidformatted="$(printf '%02d' $oldvmid)"
            # TODO: Actually the lowest free ID should be used.
            newvmid=$(assign_id)
            newvmidformatted="$(printf '%02d' $newvmid)"
            oldvmname=$(echo "$vm_info" | grep "vmName=" | sed "s|vmName=||g")
            newvmname="${oldvmname/-$oldvmidformatted-tira/-$newvmidformatted-tira}"
            userpw=$(echo "$vm_info" | grep "userPw=" | sed "s|userPw=||g")
            adminname=$(echo "$vm_info" | grep "adminName=" | sed "s|adminName=||g")
            adminpw=$(echo "$vm_info" | grep "adminPw=" | sed "s|adminPw=||g")
            newhostid="$(get_host_id)"
            newhostname="$(get_host_name)"
            newportssh=$((44400 + newvmid))
            newportrdp=$((55500 + newvmid))
            newip="10.$newhostid.$newvmid.1"
            newipvm="${newip}00"
            newiface="vboxnet$newvmid"

            tira_call vm-import "$ovafile" < /dev/null

            if [ $? != 0 ]; then
               logError "OVA file import returned error: $ovafile"
               exit 1
            fi

            VBoxManage modifyvm $oldvmname --name $newvmname
            VBoxManage hostonlyif create
            VBoxManage hostonlyif ipconfig "$newiface" --ip "$newip"
            VBoxManage modifyvm "$newvmname" --nic1 hostonly --hostonlyadapter1 "$newiface"
            VBoxManage modifyvm "$newvmname" --vrdeport "$newportrdp"

            # TODO: "store vm.txt in a config constant!, or remove this unneeded triple storing of information."
            # TODO: Move file name to conifg.
            echo "$newhostname $newvmname $newip $newportssh $newportrdp $adminname $adminpw $username $userpw" >> "$_CONFIG_FILE_tira_local_home/vms.txt"
            echo "$newhostname $newvmname" >> "$_CONFIG_FILE_tira_vms"
            patch_entry "$username" "$newhostname" "$newportssh" "$newportrdp" "$newvmid" "$newipvm" "$newvmname"

            logInfo "Done!"
        fi
    done < "$ovalist"

}

#
#    Start programm with parameters.
#
main "$@"
