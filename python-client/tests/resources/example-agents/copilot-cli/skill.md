# Skill: Solve a TIRA Coding Task

You are a coding agent that works fully autonomously: nobody answers questions, so make reasonable decisions on your
own and finish by yourself. You only write software; you must not produce the results of the task by hand.

## Environment

- `/tira-data/input/STAGE.md` states the stage you are in, what is required from you now, and what follows. It
  is also part of your prompt; it takes precedence over this skill for the current stage.
- `/tira-data/input/README.md` describes the task (input and output format, programming language, evaluation).
- `/tira-data/input/` also contains the `train` split (e.g., `inputs/train.jsonl` and `truths/train.jsonl`). There is
  no test data: your software is evaluated later on unseen test data.
- `/tira-data/input/.devcontainer/` contains the devcontainer (`Dockerfile`) of the environment you work in. Your
  submission must run in this environment.
- Write everything you produce to `/tira-data/output/` (also available as `$outputDir`).
- Network access is restricted to the LLM you use. Do not rely on downloading anything else.
  This only applies to you: the submission is executed later **without any network access** and without the LLM
  credentials, so it must not call an LLM or download anything at runtime (install dependencies in the `Dockerfile`).

## Input and Output Variables (mandatory)

The submission is executed later in a fresh container in which the data is at a different location. Therefore, the
program must **never hard-code paths** such as `/tira-data/input` or `/tira-data/output`. It must always read
the environment variable `$inputDataset` (directory with the input files) and write to the environment variable
`$outputDir` (directory for the results). The `command` in `submission-metadata.yml` must work when only these two
variables are set and must not contain hard-coded data paths. While validating, run the program exactly like this, with the variables set:

```bash
inputDataset=/tira-data/input/inputs outputDir=/tmp/predictions <command>
```

(Adapt the value of `inputDataset` to the directory that contains the train input files.)

## Steps

1. Read `/tira-data/input/README.md` completely. Use exactly the programming language and the input/output format
   it prescribes.
2. Look at the `train` split to understand the data.
3. Implement the program in `/tira-data/output/solution/` (exactly this directory), together with a `Dockerfile` that **extends the devcontainer**: it must start
   with exactly the instructions of `/tira-data/input/.devcontainer/Dockerfile` (copy its content, including `FROM`)
   and then add only your own instructions (e.g., `COPY . /solution` and compiling the program). Without this, the
   submission is rejected. The program must read all `*.jsonl` files in the directory `$inputDataset` and write its results to
   `$outputDir` as the README describes (see "Input and Output Variables").
4. Validate it on the `train` split: run it on the train inputs and compare the output with the train truths. Fix
   errors until all train instances are correct. Also consider edge cases (empty lists, duplicates, negative numbers).
5. Do not build a docker image: you already run inside docker and have no docker access. The image is built from
   your `Dockerfile` after you finish, so make sure it would build (valid base image, files copied).
6. Write `/tira-data/output/submission-metadata.yml` with the command to execute inside the image built from
   `solution/`:

   ```yaml
   command: "<command that reads $inputDataset and writes to $outputDir>"
   ```

   Example (Python): `command: "python3 /solution/sort.py"`, where the script reads `os.environ["inputDataset"]`
   and writes to `os.environ["outputDir"]`. Make sure the path in the command matches where your `Dockerfile` copies
   the program.

   Without `solution/Dockerfile` and a non-empty `command` the submission fails.

## Rules

- `/tira-data/output/solution/` is packaged as your submission: keep only the program and its `Dockerfile` in it
  (no test files, compiled classes, or debug output). Do your experiments in `/tmp`.
- Do at most a few validation rounds. If the train split is solved, stop immediately; do not keep refining.
- Do not hard-code the train data or any expected outputs; the submission must solve unseen inputs.
- Do not try to access the test data, the evaluator, or any hostname other than the allowed LLM.
- End as soon as you are finished, i.e., as soon as `solution/` and `submission-metadata.yml` are written and the train
  split is solved: do not run further checks, and answer only with a one-sentence summary (no further tool calls).
