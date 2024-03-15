Organizing Tasks
================
Get a reviewer account
----------------------
Create an account at `tira.io <https://www.tira.io/>`__ and ask an admin to add you to the
`tira_reviewer <https://www.tira.io/g/tira_reviewer>`__ group.

Create/Edit your Organization
-----------------------------

- Click on "Edit Organization" to add / edit your organization.
- In the "Edit Organization" modal, you can specify the credentials for your git integration that is used as backend in
  your tasks

Create a Docker Image for your Evaluator
----------------------------------------
An evaluator is a software that gets a system's run and the truth data as input to create the run's evaluation.

Evaluators get three variables as input in TIRA:

(1) the :code:`$inputDataset` variable contains the ground-truth data,
(2) the :code:`$inputRun` variable contains the to-be-evaluated run, and
(3) the :code:`$outputDir` variable points to the directory at which the evaluator should create the
    :code:`evaluation.prototext` file containing the evaluation results.

Evaluators should produce helpful guidance for runs that are not valid (e.g., clarify the inconsistency with a message
printed to stdout instead of failing with an exception). Users can see the output (stdout and stderr) and the evaluation
results of unblinded evaluations (in case it is a test dataset an admin manually unblinds the evaluation after ensuring
it does not leak confidential data) or all training/validation evaluations (i.e., evaluations that use a training or
validation dataset as input).

Your evaluator must be compiled as a docker image and uploaded to Docker Hub so that TIRA can load your image. Here are
some recent evaluators that you can use as blueprint for your own evaluator:

- The `huggingface evaluator <https://github.com/tira-io/hf-evaluator>`__ is an evaluator that supports all evaluations
  in huggingface evaluate. This should be the default evaluator in most cases.
- The `evaluator for multilingual stance detection of Touché23 <https://github.com/touche-webis-de/touche-code/blob/main/clef23/multilingual-stance-classification/evaluation/evaluation.py>`__
  together with `instructions on how to build the docker image <https://github.com/touche-webis-de/touche-code/tree/main/clef23/multilingual-stance-classification#build-the-evaluator>`__
- The `clickbait-spoiling-eval.py <https://github.com/pan-webis-de/pan-code/blob/master/semeval23/clickbait-spoiling-eval.py>`__
  script used in the Clickbait Spoiling task at SemEval 23 together with `instructions on how to build the docker image <https://github.com/pan-webis-de/pan-code/tree/master/semeval23#development>`__
  and the `command to add in TIRA <https://github.com/pan-webis-de/pan-code/tree/master/semeval23#integration-in-tira>`__.
- The `ValueEval 2023 evaluator <https://github.com/touche-webis-de/touche-code/tree/main/semeval23/human-value-detection/evaluator>`__
  used in SemEval-2023.
- `ir_measures <https://github.com/tira-io/ir-experiment-platform/tree/main/ir-measures>`__ for the evaluation of IR
  experiments.

Add a new Task and new Datasets to TIRA
---------------------------------------
We assume that you have `a reviewer login to tira <#get-a-reviewer-account>`__, the dataset, and the
`evaluator <#create-a-docker-image-for-your-evaluator>`__ for your task ready.

- Visit the overview of all tasks at `tira.io <https://www.tira.io/>`__
- Click on "Add Task" and fill out the corresponding form (use the Master VM Id that you received during registration,
  e.g., :code:`princess-knight` was a baseline in Touché)
- Click on your newly created task
- Click on "Add a new Dataset" and fill out the corresponding form
- Navigate to the Evaluator section of your new dataset. Click on "Git CI" to use the CI backend and specify the Docker
  image of the evaluator and the `evaluation command <#create-a-docker-image-for-your-evaluator>`__.

Provide Public Baselines to Simplify Participation
--------------------------------------------------
In the best case, you provide the code, a published docker image, and instructions on how to compile the code into a docker image to simplify participation in your shared tasks.

We have some examples on baselines that you can adopt for your shared task, e.g.:

- The `clickbait spoiling baselines from SemEval-2023 <https://github.com/pan-webis-de/pan-code/tree/master/semeval23/baselines>`__
- The `ValueEval baseline from SemEval-2023 <https://github.com/touche-webis-de/touche-code/tree/main/semeval23/human-value-detection/1-baseline>`__
- The baselines for `Touché-2023 at CLEF <https://github.com/touche-webis-de/touche-code/tree/main/clef23/evidence-retrieval-for-causal-questions/baseline-pyterrier>`__
- The baseline for `PAN-2023 at CLEF <https://github.com/pan-webis-de/pan-code/tree/master/clef23/trigger-detection/baselines>`__

To simplify testing software submissions locally before they are uploaded to TIRA, we provide a :code:`tira-run` command
that participants can use to test their image locally. The :code:`tira-run` commands executes a software as it would be
executed in TIRA.

You can find some examples of shared tasks that use :code:`tira-run` in their baselines to simplify participation here:

- https://github.com/touche-webis-de/touche-code/tree/main/clef23/evidence-retrieval-for-causal-questions/baseline-pyterrier
- https://github.com/touche-webis-de/touche-code/tree/main/clef23/multilingual-stance-classification

We recommend that you have for all of your baselines an :code:`tira-run` example so that you can point participants to
this example if their software submission fails in TIRA. For this, you need:

- The baseline should be publicly available, e.g., at Dockerhub
- You need a small sample of the data (can be artificial, but must have the same structure/format as the test data)

Assuming that you have published the baseline for your task at dockerhub under the name :code:`<DOCKER_IMAGE_BASELINE>`
and that the baseline is executed via the command :code:`<BASELINE_SOFTWARE_COMMAND>` inside the container and that you
have a directory :code:`tira-sample-input` with the sample data in the git repository of your baseline, you can add the
following documentation (replace the placeholders with the correct values) to your README:

.. code::

    You can test docker images that you would submit to TIRA locally via `tira-run`. 
    The `tira-run` commands executes a software as it would be executed in TIRA (i.e., with sandboxing using the same command pattern).

    We recommend that you test your software locally on the sample dataset `tira-sample-input` before uploading it to TIRA to ensure that your software works correctly (this also simplifies debugging as everything is under your control and runs on your machine).

    Please install `tira-run` via `pip3 install tira`.

    After `tira-run` is installed, you can execute the baseline on the sample dataset `tira-sample-input` via this command:
    `tira-run --input-directory ${PWD}/tira-sample-input --image <DOCKER_IMAGE_BASELINE> --command <BASELINE_SOFTWARE_COMMAND>`

    This command should create the following output in `tira-output`: <TODO_ADD_EXAMPLE_OUTPUT>

Modifying virtual machines
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Login to the machine where the VM exists (:code:`ssh tira@betawebXYZ``)
- Locate the complete :code:`[vmName]` from :code:`tira/model/users/[users].prototext`.
- RAM
    On dockerized tira hosts: enter the docker container. You can do this using:

    .. code:: bash

        docker exec -ti $(docker ps|grep 'tira-io/tira-host'|awk '{print $1}') bash

    Then run:

    .. code:: bash

        tira vm-shutdown [userId]
        VBoxManage modifyvm [vmName] --memory [MBs]
        tira vm-start [userId]

- CPUs
    On dockerized tira hosts: enter the docker container. You can do this using:

    .. code:: bash

        docker exec -ti $(docker ps|grep 'tira-io/tira-host'|awk '{print $1}') bash

    Then run:

    .. code:: bash

        tira vm-shutdown [userId]
        VBoxManage modifyvm [vmName] --cpus [number]
        tira vm-start [userId]

- HDD space (read/write from VM, is sandboxed along with VM)
    On dockerized tira hosts: enter the docker container. You can do this using:

    .. code:: bash

        docker exec -ti $(docker ps|grep 'tira-io/tira-host'|awk '{print $1}') bash

    Then run:

    .. code:: bash

        cd /home/tira/VirtualBox\ VMs/[virtualMachineId]
        tira vm-stop $(basename "$PWD")
        VBoxManage createhd --filename data.vmdk --format VMDK --size [MBs]
        # In the following: if "SATA" does not work, try "SATA Controller" or "SATAController"
        VBoxManage storageattach $(basename "$PWD") --storagectl "SATA" --port 1 --type hdd --medium data.vmdk
        tira vm-start $(basename "$PWD")
        tira vm-ssh $(basename "$PWD")
    
    Use :code:`fdisk -l` to check that the new partition is indeed "/dev/sdb". Adjust below instructions otherwise.
    
    .. code:: bash
    
        sudo parted -s -a optimal /dev/sdb mklabel gpt -- mkpart primary ext4 1 -1
        sudo mkfs -t ext4 /dev/sdb1
        sudo mkdir /mnt/data
        sudo nano /etc/fstab</code> and add <code>/dev/sdb1 /mnt/data ext4 defaults 0 2
        sudo mount /dev/sdb1

- HDD space (read-only from VM, is not sandboxed)
    Follow `these instructions <https://git.webis.de/code-generic/code-saltstack/blob/master/src/srv/salt/pillars/tira-sftp-users.sls>`__.
    Then run

    .. code:: bash

        tira vm-shutdown [userId]
        VBoxManage sharedfolder add [virtualMachineId] --name data --hostpath /home/[userId]/data --readonly --automount
        tira vm-start [userId]

    .. note::
        This allows connections by SFTP, but not by SSH (as the home directory is not writable)

Moderate a Task:
----------------
(1) Log in to tira.io with a reviewer account. 
(2) (optional) Add a new organizer using :code:`Add organizer` on the website. 
(3) Create a master-vm (see `Set up the master VM`_)
(4) Reload the VMs on the Admin Panel on the website.
(5) Add a new task using :code:`Add Task` on the website. Requires a master-vm
(6) Add a new dataset using :code:`Add Dataset` on the page of the respective task. You can also add the evaluator data
    during this step.
(7) Install the evaluator on the master-vm in accordance to the data entered during step. 6

Set up the master VM
~~~~~~~~~~~~~~~~~~~~
(1) Create the virtual machine using :code:`tira vm-create`. The name should end with *-master*.
(2) Connect to the TIRA host container:

    .. code:: bash
        
        docker exec -ti $(docker ps | grep 'tira-io/tira-host' | awk '{print $1}') bash
(3) Give yourself permission to the VM's group on tira.io (if you followed [the instructions](#get-a-reviewer-account))
(4) Give the master VM access to the test and truth directories.
    
    .. code:: bash
        
        vboxmanage sharedfolder add [virtualMachineId] --name [typeDirectory] --hostpath [typeDirectoryPath] --readonly --automount
    
    This should be done for **training-datasets-truth, test-datasets, and test-datasets-truth**


Troubleshooting
~~~~~~~~~~~~~~~
.. collapse:: Changes do not show up on the website

    Go to `tira-admin <https://tira.io/tira-admin>`__ and then to :code:`System Actions > Reload Data`.

.. collapse:: Error on creating a virtual machine: :code:`VBoxNetAdpCtl: Error while adding new interface: failed to open /dev/vboxnetctl: No such file or directory`,
    usually comes with an error on vm start: :code:`Nonexistent host networking interface, name 'vboxnetXX'`.

    - Log in as webis
    - Check if /dev/vboxnetctl exists <code>ls /dev/vboxnetctl</code>. If not, proceed. If yes, there is a different
      error.
    - Run <code>sudo modprobe vboxnetadp</code>
    - Run <code>sudo modprobe vboxpci</code> (needs to be a separate call like here!)
    - To check if VMs are running run <code>sudo -H -u tira VBoxManage list runningvms</code>
    - If so, run <code>tira stop</code>
    - Wait a few seconds
    - Run <code>sudo service vboxdrv restart</code>
    - Run <code>tira start</code>

.. collapse:: A virtual machine does not :code:`tira vm-start` with error :code:`is not a valid username/vmname`.

    The :code:`vbox` file might be lost. Go to :code:`/home/tira/VirtualBox VMs/**vm-name**`. If there is a
    :code:`.vbox-prev` but no :code:`.vbox` file, copy the former to create the latter (effectivley restoring it).

.. collapse:: Read-only file system in a virtual machine.

    Restart the virtual machine

.. collapse:: A virtual machine has :code:`/media/training-datasets/` not mounted.

    On betaweb020:
    
    .. code:: bash

        sudo salt '**server**' state.apply tira

    Then maybe it is needed to restart the VM

.. collapse:: Prometheus says there are errors in :code:`vboxmanage list vms --long`

    Perform maintenance: "Removal of inaccessible VMs"
