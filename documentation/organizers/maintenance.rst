Maintenance
===========

Virtual Machine Backup
----------------------
There are two steps to backing up a virtual machine: Backing up the appliance, and backing up all user metadata
associated with that machine on TIRA.

Backing up the appliance
~~~~~~~~~~~~~~~~~~~~~~~~
Run the following command on the host where the machine is hosted

.. code:: bash

    tira vm-backup vmname username

Make sure the machine is backed up on ceph under :code:`<tira-model>/backup`.

Now delete the machine from the host by running:

.. code:: bash

    tira vm-delete vmname

Backing up the appliance
~~~~~~~~~~~~~~~~~~~~~~~~
Backup all user metadata by running:

.. code:: bash

    ./usr/lib/tira/tira-vm-info-backup.py -u username -b

and confirming when prompted.

.. note::
    You might need to install the :code:`rich` and :code:`click` packages if those are not yet installed on that
    particular host. To install these, simply run

    .. code:: bash

        pip3 install rich click

Migration of VM's between hosts
-------------------------------
1. Run the following shell-commands on the **old** host:
    .. code:: bash

        ~$ tira vm-stop <vm name>
        ~$ VBoxManage export <vm name> -o <vm name>.ova
        ~$ scp <vm-name>.ova <user>@<host>:/home/tira/VirtualBox\ VMs/<vm-name>.ova

2. Run the following shell-commands on the **new** host:
    .. code:: bash

        ~$ VBoxManage import <vm name>.ova
        ~$ rm <vm name>.ova
        ~$ nano /home/tira/.tira/vms.txt

    - Transfer the line corresponding to :code:`<vm name>` from old host to new host.
    - Change host name to new host.
    - Change the <vm id> from old host to the id of a new vm on new host.
    - Change IP and ports corresponding to new id.

3. From configure VM script:
    .. code:: bash

        ~$ VBoxManage hostonlyif create   # (if needed)
        ~$ VBoxManage hostonlyif ipconfig "vboxnet<id>" --ip "10.<host id>.<id>.1"
        ~$ VBoxManage modifyvm "<vm name>" --nic1 hostonly --hostonlyadapter1 "vboxnet<id>"
        ~$ VBoxManage modifyvm "<vm name>" --vrde on
        ~$ VBoxManage modifyvm "<vm name>" --vrdeport "555<0-padded id>"
        ~$ VBoxManage modifyvm "<vm name>" --vrdeauthtype external

4. Tira-model:
    .. code:: bash

        ~$ nano <tira-model>/model/virtual-machines/virtual-machines.txt
        # Change host and vm name to correspond to new host and name.
        ~$ nano <tira-model>/model/users/users.txt
        ~$ nano <tira-model>/model/users/<vm name>.txt
        # Change vm name, vm id, ports, and host to correspond to new host and names.

.. caution::
    Hard disk drive name cannot be changed and will include the old host vm id.


Backup of all VMs on one host
-----------------------------
.. code:: bash

    for f in *-tira-*; 
        do u=$(echo "$f" | awk -F '-[0-9][0-9]-' '{print $1}'); 
        tira vm-backup $f $u;  
    done

Recycling a Username
--------------------
If you need to re-use an old username, which might occur if you accidentally create a VM with the wrong .ova file,
follow these steps:

1. Delete the corresponding virtual machine by running :code:`tira vm-delete <vm-name>`
2. Remove the corresponding user block from the following file: :code:`<tira-model>/model/users/users.prototext`
3. Delete the :code:`<username>.prototext` file from the :code:`<tira-model>/model/virtual-machines/` directory.

Helpful commands
----------------
Recreate size files
~~~~~~~~~~~~~~~~~~~

.. code:: bash

    for f in ls -d */*/*; do
    if [ -d "$f/output" ]; then
        find $f/output -type f -exec cat {} + | wc -l >> $f/size.txt
        find $f/output -type f | wc -l >> $f/size.txt
        find $f/output -type d | wc -l >> $f/size.txt
    fi
    done

Recreate file-list files
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    for f in ls -d */*/*; do
    if [ -d "$f/output" ]; then
        tree -ahv $f/output > $f/file-list.txt
    fi
    done

Exchange strings
~~~~~~~~~~~~~~~~

.. code:: bash

    find -type f -name "*.prototext" -exec grep "corpus" {} \;
    find -type f -name "*.prototext" -exec sed -i "s/corpus/dataset/g" {} \;
    find -type f -name "*.prototext" -exec sed -i "s/Corpus/Dataset/g" {} \;
    find -type f -name "*.prototext" -exec sed -i "s/corpora/datasets/g" {} \;
    find -type f -name "*.prototext" -exec sed -i "s/Corpora/Datasets/g" {} \;
    find -type f -name "run*.bin" -exec rm {} \;
    find -type f -name "evaluation.bin" -exec rm {} \;
    rename s/corpus/dataset/ *
