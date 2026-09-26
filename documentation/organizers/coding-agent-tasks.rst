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
    ├── task-name-01/
    │   ├── README.md
    │   └── .devcontainer/
    ├── task-name-02/
    │   ├── README.md
    │   └── .devcontainer/
    └── task-name-n/
        ├── README.md
        └── .devcontainer/

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

.. hint:: No dedicated example task is available yet. If you are organizing a shared task that evaluates coding
   agents, please reach out so we can document your setup here.
