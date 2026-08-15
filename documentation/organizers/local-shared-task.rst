.. _local_shared_task:

Set Up a Shared Task Locally with a Coding Agent
=================================================

This guide describes how to prepare and validate a shared task in a Git repository before creating it on TIRA.
It is written so that you can follow it yourself or give the steps to a coding agent.

The local workflow validates the complete path through the task:

1. package system inputs and private truth data,
2. describe both partitions in a Hugging Face dataset card,
3. validate their formats,
4. build and run a baseline in Docker,
5. validate the baseline output, and
6. run the evaluator on that output.

Nothing is uploaded when ``--dry-run`` is used.

Prerequisites
-------------

Install Python, Git, and Docker. Docker must be running to test the baseline and a containerized evaluator. Install the
Python dependencies with:

.. code-block:: bash

   python3 -m pip install tira datasets huggingface_hub

Create a Git repository for the task. Do not put credentials, API tokens, or confidential test data into prompts,
commits, or agent instruction files.

Step 1: Give the Agent a Bounded Task
-------------------------------------

Tell the coding agent what it may change and how completion will be measured. For example:

.. code-block:: text

   Set up a TIRA shared-task dataset in datasets/my-task-smoke-test.

   Requirements:
   - Keep system inputs and truth data in separate dataset-card configurations.
   - Add a tiny, non-confidential smoke-test dataset.
   - Add a deterministic baseline and evaluator.
   - Package the evaluator as a Docker image.
   - Use the output filename predictions.jsonl.
   - First validate packaging with:
     tira-cli dataset-submission --path datasets/my-task-smoke-test \
       --task my-task --split train --dry-run --skip-baseline
   - Then validate the complete baseline and evaluator workflow without
     --skip-baseline.
   - Do not upload anything and do not use credentials.
   - Document every command needed to reproduce the validation.

An ``AGENTS.md`` file at the repository root is useful for durable instructions. Include the expected input and output
formats, commands that must pass, files the agent must not modify, and whether network access or Docker is available.

Step 2: Create the Repository Layout
------------------------------------

A practical layout keeps the dataset, baseline, and evaluator independently testable:

.. code-block:: text

   shared-task/
   |-- AGENTS.md
   |-- README.md
   |-- datasets/
   |   `-- my-task-smoke-test/
   |       |-- README.md
   |       |-- inputs/
   |       `-- truths/
   |-- baseline/
   |   |-- Dockerfile
   |   `-- ...
   `-- evaluator/
       |-- Dockerfile
       `-- ...

Start with a tiny public smoke-test dataset. It should have the same file names and structure as the final dataset but
only enough instances to make local execution fast. Add confidential data only after the workflow works with artificial
or public data.

Step 3: Describe the Dataset
----------------------------

The dataset directory must have a ``README.md`` containing a Hugging Face dataset card. Its YAML front matter defines
which files become system inputs, which files become truths, and how TIRA validates and evaluates a run.

The following is a structural template. Replace the format names, commands, paths, and image with values supported by
your task:

.. code-block:: yaml

   ---
   configs:
   - config_name: inputs
     data_files:
     - split: train
       path: "inputs/**"
   - config_name: truths
     data_files:
     - split: train
       path: "truths/**"

   tira_configs:
     resolve_inputs_to: "inputs"
     resolve_truths_to: "truths"
     default_upload_name: "predictions.jsonl"

     input_format:
       name: "<registered-input-format>"
     truth_format:
       name: "<registered-truth-format>"

     baseline:
       link: "../../baseline"
       command: "<baseline-command> --input $inputDataset --output $outputDir"
       format:
         name: "<registered-run-format>"

     evaluator:
       image: "ghcr.io/<owner>/<evaluator>:<version>"
       command: "<evaluator-command> --input ${inputRun} --truths ${inputDataset} --output ${outputDir}"
   ---

   # My Task Smoke Test

   Explain the task, file formats, license, and origin of the data here.

``default_upload_name`` is required and specifies the filename TIRA suggests for participant uploads. The
``inputs`` configuration is exposed to submitted systems. The ``truths`` configuration is only exposed to the
evaluator.

The examples in the TIRA repository are useful starting points that track the current client requirements:

* `Learned Sparse Retrieval <https://github.com/tira-io/tira/tree/main/python-client/tests/resources/example-datasets/learned-sparse-retrieval>`_
* `Multi-Author Analysis <https://github.com/tira-io/tira/tree/main/python-client/tests/resources/example-datasets/multi-author-analysis>`_
* `Kiddy RAG Spot Check <https://github.com/tira-io/tira/tree/main/python-client/tests/resources/auto-judge/kiddy-rag>`_

The following definitions show how recent shared tasks apply the same pattern to different data layouts:

* `Touché 2026 Causality Extraction Spot Check <https://github.com/touche-webis-de/touche-code/tree/main/clef26/causality-extraction/task1-spot-check-dataset>`_
  uses separate JSONL files, built-in evaluation measures, and a minimal classification baseline.
* `PAN 2026 Multi-Author Analysis Smoketest <https://github.com/pan-webis-de/pan-code/tree/master/clef26/multi-author-analysis/smoketest>`_
  separates nested inputs and truths with glob patterns and configures a custom evaluator image.
* `LongEval 2026 Scientific Retrieval Spot Check <https://github.com/clef-longeval/longeval-code/tree/main/clef26/tira-setup/task-1-spot-check>`_
  combines documents, queries, metadata, and TREC qrels in a retrieval task with a custom output format.

.. note::

   These external repositories evolve independently. At the time of writing, their dataset cards illustrate the
   structure but do not yet define the now-required ``tira_configs.default_upload_name``. Add it before validating a
   copied definition with the current TIRA client.

Step 4: Validate Dataset Packaging
----------------------------------

Run the first dry run without building the baseline:

.. code-block:: bash

   tira-cli dataset-submission \
     --path datasets/my-task-smoke-test \
     --task my-task \
     --split train \
     --dry-run \
     --skip-baseline

Do not pass ``.`` or ``..`` to ``--path``. The directory name is used as the dataset name.

This validation checks that:

* the dataset card can be loaded,
* the requested split exists,
* system inputs and truths resolve to separate directories,
* ``default_upload_name`` is present, and
* both partitions match their configured formats.

Ask the agent to fix the cause of every error rather than weakening format checks or excluding problematic files.

Step 5: Implement the Baseline
------------------------------

The baseline is the executable specification of what a valid participant submission looks like. It should:

* read only from ``$inputDataset``,
* write only to ``$outputDir``,
* produce the configured run format,
* run without interactive input, and
* finish quickly on the smoke-test dataset.

``baseline.link`` can point to a baseline directory relative to the directory containing the dataset ``README.md``.
For the repository layout above, use ``../../baseline``. This keeps local validation self-contained and does not
require pushing the baseline first.

Alternatively, ``baseline.link`` can use a public GitHub directory URL such as
``https://github.com/<owner>/<repository>/tree/main/baseline``. The complete dry run clones that repository before
building the image. Relative paths must identify an existing directory; absolute filesystem paths are not supported.

If the baseline uses a non-default Dockerfile, specify it with ``baseline.file``. For a relative baseline link, this
path is relative to the linked baseline directory. For a GitHub link, it remains relative to the cloned repository
root.

For concrete implementations, compare the minimal `Touché Causality Extraction baseline
<https://github.com/touche-webis-de/touche-code/tree/main/clef26/causality-extraction/task1-naive-baseline>`_
with the more extensive `LongEval PyTerrier baseline
<https://github.com/clef-longeval/longeval-code/tree/main/clef25/pyterrier-baseline>`_. Both expose the TIRA input and
output directories as command-line arguments, but demonstrate different levels of complexity.

Step 6: Implement and Test the Evaluator
----------------------------------------

An evaluator receives:

* ``$inputRun``: the baseline or participant output,
* ``$inputDataset``: the truth partition, and
* ``$outputDir``: the directory for evaluation results.

The evaluator should reject malformed runs with a useful message, produce deterministic results, and write a valid
``evaluation.prototext`` file. Add unit tests for valid, malformed, and incomplete runs before packaging it.

If the task uses standard IR measures, the dataset card can define ``evaluator.measures`` instead of a custom evaluator
image and command. Otherwise, package the evaluator as a Docker image.

The `Touché 2026 Causality Extraction evaluator
<https://github.com/touche-webis-de/touche-code/tree/main/clef26/causality-extraction/task3-evaluator>`_ is a compact
example of an evaluator Dockerfile and a script that writes ``evaluation.prototext``. The `PAN 2026 Multi-Author
Analysis evaluator
<https://github.com/pan-webis-de/pan-code/tree/master/clef26/multi-author-analysis/evaluator>`_ additionally includes
unit tests for its scoring logic.

Step 7: Build and Publish the Evaluator Image
---------------------------------------------

Build the evaluator image with a versioned tag:

.. code-block:: bash

   docker build \
     --tag ghcr.io/<owner>/<evaluator>:<version> \
     evaluator/

Test the image against the smoke-test truths and a known valid run. The evaluator container must work without network
access and should not write outside ``$outputDir``.

After the local test succeeds, publish the image to a registry accessible to TIRA:

.. code-block:: bash

   docker push ghcr.io/<owner>/<evaluator>:<version>

Use the exact tag in ``tira_configs.evaluator.image``. Do not use ``latest`` for a final task: a pinned version keeps
past evaluations reproducible. The complete local dry run ensures that this image is available locally and executes it
with TIRA's evaluator mounts and sandboxing.

Step 8: Validate the Complete Workflow
--------------------------------------

After the baseline is available at the relative path or GitHub URL in the dataset card and the evaluator image is
available, run the same command without ``--skip-baseline``:

.. code-block:: bash

   tira-cli dataset-submission \
     --path datasets/my-task-smoke-test \
     --task my-task \
     --split train \
     --dry-run

The task is locally ready when this command successfully packages both data partitions, builds and executes the
baseline, validates its output, and evaluates it with the configured evaluator.

Record the successful command, evaluator image digest, and relevant tool versions in the repository README so another
person or agent can reproduce the result.

Step 9: Review Before Uploading
-------------------------------

Before removing ``--dry-run``:

* inspect the generated input and truth archives,
* confirm that no truth labels occur in the system-input archive,
* confirm that all files may legally be uploaded and processed,
* review container images and dependencies,
* test with a clean checkout, and
* have a human review the task metadata and evaluation results.

Uploading requires organizer permissions and an authenticated TIRA client. Follow :doc:`organizing-tasks` for creating
the task on TIRA and managing its datasets after local validation.
