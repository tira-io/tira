TIRA for Evaluating Coding Agents
=================================

.. warning::

    This page is still work in progress.

TIRA can be used to organize shared tasks that evaluate coding agents. Instead of participants submitting runs or
software directly, participants submit a coding agent that autonomously *writes* the software that solves a task.
TIRA then executes the agent, packages whatever it produces into a submission, and evaluates that submission like
any other TIRA submission.

.. tip::

   Start with :doc:`local-shared-task` to prepare the dataset and devcontainer configuration in a Git repository
   and validate the complete workflow locally before uploading anything to TIRA.

What is a Coding Agent?
------------------------

In TIRA, a coding agent is defined solely via an ``Agents.md`` file. This file describes, in natural language, how
the agent should approach a task; it contains no task-specific logic and is not allowed to submit results. Beyond
that, an agent must run without human feedback: once started, it works fully autonomously and terminates on its
own, producing a docker image and a command as its submission.

Dataset Structure for Coding Agent Tasks
------------------------------------------

A dataset for coding agent tasks is a directory of independent tasks:

.. code-block:: text

    my-dataset/
    ├── README.md
    ├── task-name-01/
    │   ├── README.md
    │   └── .devcontainer/
    ├── task-name-02/
    │   ├── README.md
    │   └── .devcontainer/
    └── task-name-n/
        ├── README.md
        └── .devcontainer/

The ``README.md`` of the dataset declares its tasks in the YAML front matter (and can contain a human-readable
overview):

.. code-block:: yaml

    ---
    tasks:
      - name: task-name-01
        path: task-name-01
        language: Python
      - name: task-name-02
        path: task-name-02
        language: Java
    ---

Each ``task-name-i`` directory contains:

- A ``README.md`` with a `Hugging Face dataset card <https://huggingface.co/docs/hub/datasets-cards>`_ that
  defines a ``train`` split, a ``test`` split, and the evaluation used to score submissions for this task.
- A `devcontainer configuration <https://containers.dev/>`_ that defines the sandboxed environment in which the
  agent is executed.

Execution Workflow
--------------------

Solving a task with a coding agent happens in two phases:

1. **Agent phase.** The agent (i.e., ``Agents.md``) is executed inside the task's devcontainer. Within this
   sandbox, the agent has access only to the LLM it is configured to use (see
   :doc:`../participants/llms-via-rest-api` for how to forward LLM credentials safely), the task's training data,
   and the task's ``README.md`` with the dataset card definitions (train/test splits, evaluation) stripped out, so
   that the agent only sees the human-readable task description. The agent works autonomously to produce a docker
   image and a command that solve the task.
2. **Evaluation phase.** The docker image and command produced by the agent are treated as a regular TIRA
   submission: they are executed on the task's ``test`` split, and the result is scored with the evaluation
   defined in the task's dataset card, exactly as for any other TIRA submission.

Setting Up a Coding Agent Task
---------------------------------

The general workflow follows the same steps as :doc:`organizing-tasks`:

1. Prepare a dataset with one directory per task, each containing a dataset-card ``README.md`` (with ``train`` and
   ``test`` splits and an evaluation) and a devcontainer configuration.
2. Build an evaluator that consumes the docker image and command produced by the agent, executes them on the
   ``test`` split, and produces a score, as described in the dataset card.
3. Optionally provide a baseline ``Agents.md`` that participants can use as a starting point.
4. Add the task and dataset to TIRA as described in :doc:`organizing-tasks`.

A task can have multiple train and test datasets (e.g., different input distributions). The splits ``train`` and
``test`` are required, additional splits are named ``train-<name>`` and ``test-<name>`` (e.g., ``train-02``,
``test-02``), any other split name is rejected. The agent sees all train splits, and its submission is run and
evaluated on every test split separately (``05-predictions-test-02/``, ``06-results-test-02/``; the results of
``test`` are in ``05-predictions/`` and ``06-results/``). All splits of a task use the same evaluator. Splits can be
described in the front matter of the dataset card; the descriptions of the train splits are shown to the agent, those
of the test splits only appear in the result summary:

.. code-block:: yaml

    tira_configs:
      split_descriptions:
        train: "Short lists."
        train-02: "Long lists."
        test: "Short lists, as in train."
        test-02: "Edge cases: empty lists and duplicates."

The ``path`` of a split in ``configs`` may also be a list of files (e.g., a data file and its ``config.json``). The agent
sees them under their relative paths; for a test split, all files are placed next to each other (flat, by file name) in
the input and truth directories of the submission and the evaluator. See ``coding-agent-sisap-2026`` for an example.

Run an agent on all tasks of a dataset locally with
``tira-cli run coding-agent --path <dataset-directory> --agent <agent-directory>``
(use ``--forward-environment-variable`` for API keys). The agent is not part of the dataset. How the Copilot CLI is run
and the smoke-test steps are built into ``tira-cli``; the agent directory defines the agent: a ``skill.md`` that tells
the agent how to work, plus any other files it may use (e.g., reference implementations or papers), mounted read-only at
``/tira-agent`` (see ``python-client/tests/resources/example-agents/copilot-cli``).
``tira-cli dataset-submission ... --dry-run`` only validates the packaging.

The ``sandboxed-coding-agent`` workflow of ``tira-cli`` implements this setup. Its ``workflow_configuration`` takes:

- ``task_directory``: a single task directory with the ``README.md`` dataset card (``train``/``test`` splits for the
  ``inputs`` and ``truths`` configs). Alternatively, pass ``dataset_directory`` (exactly one of both) to run all
  tasks declared in the dataset's ``README.md``; the result then has one sub-directory per task.
- ``allowed_hostnames``: the only hostnames (e.g., of the LLM API) the agent may reach. Hostnames of forwarded ``COPILOT_PROVIDER_BASE_URL`` / ``OPENAI_BASE_URL`` variables are added automatically. Use fully qualified names, as they are resolved inside docker.
- ``agent_steps``: optional list of ``{name, command}`` smoke tests that run first in the agent container; a failing step ends the task (in dataset mode, the remaining tasks are still run). ``stop_after_step`` stops after the named step. ``agent_directory`` is mounted read-only at ``/tira-agent`` and ``runner_directory`` at ``/tira-runner``.
- ``agent_retries`` (default 5): how often the agent is started again if its result is invalid (e.g., no ``submission-metadata.yml``, or the ``Dockerfile`` does not extend the devcontainer) or its submission can not be built, run, or evaluated on the test split (e.g., a syntax error, or no predictions). The agent gets the rejected output mounted at ``/tira-data/output`` and the reason in ``/tira-data/input/feedback/feedback.md`` (for failed test runs with the ``stdout.txt`` and ``stderr.txt`` of the run next to it, so avoid logging test data). Rejected attempts are kept as ``NN-result-attempt-K/``, ``05-predictions-attempt-K/``, and ``06-results-attempt-K/``.
- ``review_rounds`` (default 5): how often the agent reviews a successful evaluation. It is told that its submission ran on unseen test data and gets ``/tira-data/input/feedback/`` with ``feedback.md``, ``stdout.txt``, ``stderr.txt``, and ``evaluation.prototext`` (so the test scores are visible to the agent). If it changes its solution, the new solution is built, run, and evaluated again (this uses a round); an unchanged solution ends the review. Set to 0 to disable.
- If ``software`` has no ``image``, the agent is started in the image of the task's ``.devcontainer/devcontainer.json`` (``image`` or ``build.dockerfile``).
- ``evaluator_image`` and ``evaluator_command`` (optional): override ``tira_configs.evaluator`` of the dataset card.
  As for ``tira_configs.evaluator.image`` in the dataset card, the image can be a pullable image reference, a directory
  relative to the task directory, or a git ``.../tree/main/<dir>`` link. Directories and links are built into a docker
  image automatically (this requires ``gitpython`` and the code to be in a git repository).

The software is the agent (``image`` and ``command``). In the agent phase it only sees the ``train`` split and the
task ``README.md`` without its front matter. It must write its source code with a ``Dockerfile`` to ``solution/`` and a
``submission-metadata.yml`` with the ``command`` that runs it (the agent has no docker access, the workflow builds the
image). The task's ``.devcontainer`` is mounted at ``/tira-data/input/.devcontainer`` and the ``Dockerfile`` of the
solution must start with the instructions of the devcontainer (checked by the workflow). In the evaluation phase, this
docker submission runs without network access on the ``test`` inputs and is scored by the evaluator.

The results per task are ``01-<step>/`` ... ``NN-result/`` (``source-code.zip``, ``submission-metadata.yml``,
``stdout.txt``, ``stderr.txt``, ``network-access.log``), then ``05-predictions/`` and ``06-results/``. Each run
records what it was given, so that the input of every stage can be inspected afterwards:

- ``<stage>/input/STAGE.md``: the stage description the agent was given at ``/tira-data/input/STAGE.md``: the pipeline with the
  position of the current run (smoke test, first solution, retry k of n, review round k of n), what is required in this
  stage, and the files it gets. Agents should include it in their prompt (the example agent does).
- ``<stage>/input/README.md``: the task description exactly as the agent saw it (without front matter).
- ``<stage>/input/feedback/``: the feedback files of this run (``feedback.md``, and for retries/reviews also
  ``stdout.txt``, ``stderr.txt``, and ``evaluation.prototext``).
- ``<stage>/input/manifest.txt``: the other files mounted to the agent (the ``train`` split and the devcontainer)
  with their sizes; they are not duplicated.
- ``<stage>/command.txt``: the exact command executed for the stage.
- ``<stage>/prompt.txt``: the exact prompt of the agent, if the agent writes it to ``prompt.txt`` in its output
  directory (the example agent does this; agents that do not record it leave only ``input/`` and ``command.txt``).

Each task directory also contains a ``summary.md`` (a checklist of what worked and what failed, the problem of the first
failed stage with a to-do, and a description of every directory, e.g., whether an ``-attempt-K`` run was rejected or
only reviewed). The top level of the results has a ``README.md`` explaining the layout and, for datasets, a
``summary.md`` with the status of all tasks.

With ``stop_after_step: result`` the workflow stops after the result of the first task.

Example tasks (Python, Java, Julia) are available in
``python-client/tests/resources/example-datasets/coding-agent-sorting-tasks/``.

Running the Example
-------------------

The following runs the Python sorting example with a trivial "agent" that just copies the baseline as its solution. It
needs Docker and the ``tira`` Python package (with ``gitpython``), and the example is run from ``python-client/``. The
evaluator and the submission are built automatically.

Run the workflow. The "agent" is a shell command that writes ``solution/`` and ``submission-metadata.yml``; a real agent would instead be
an image with your coding agent (and use ``forward_environment_variables`` for its API key).

.. code-block:: python

    from tira.local_client import Client
    from tira.workflows import run_workflow

    result = run_workflow(
        system_inputs=".",
        tira=Client(),
        workflow="sandboxed-coding-agent",
        workflow_configuration={
            "task_directory": "tests/resources/example-datasets/coding-agent-sorting-tasks/sorting-python",
            "allowed_hostnames": ["api.openai.com"],
            "agent_directory": "tests/resources/example-datasets/coding-agent-sorting-tasks/sorting-python/baseline",
            "evaluator_image": "evaluator",
            "evaluator_command": "python3 /evaluate.py --predictions $inputRun --truths $inputDataset --output $outputDir",
        },
        software={
            "image": "python:3.12-slim",
            "command": "mkdir /tira-data/output/solution && cp /tira-agent/sort.py /tira-agent/Dockerfile /tira-data/output/solution/ && echo 'command: python3 /sort.py --input /tira-data/input --output /tira-data/output' > /tira-data/output/submission-metadata.yml",
        },
    )
    print(result.level, result.message, result.run)

On success, the message contains the ``evaluation.prototext`` (here, an exact-match accuracy of ``1.0``), and
``result.run`` points to a directory with the output of each phase (``01-result``, ``05-predictions``,
``06-results``). The agent phase starts a network proxy container (pulled on first use) that only allows the
configured ``allowed_hostnames``.

.. note:: If you run this from inside a container, share the temporary directory with the Docker host (e.g.,
   ``docker run -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/tmp ...``), as the workflow mounts temporary
   directories into the containers it starts.
