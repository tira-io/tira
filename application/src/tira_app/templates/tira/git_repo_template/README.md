# Code Submission Github Repository for Task {{ task_id }}

This is a git repository template for code submissions to the shared task {{ task_id }} in TIRA.

This repository explains how to configure a Github action for your code submission.
The corresponding Github action is [.github/workflows/upload-software-to-tira.yml](.github/workflows/upload-software-to-tira.yml).

You must copy it to the .github/workflows of your own repository and adjust it to your code.

The rest of this repository explains how the Github action works with a minimal example, so that you can test it on your machine but also directly by running the action in your own repository.

The github action makes the following steps:

(1) Install dependencies, i.e., install python, tira (`pip3 install tira`) and Docker.

(2) Build the Docker image: (you might have to modify the Dockerfile, e.g., add your own code, install other dependencies, etc.

```
docker build -t {{ image }} -f Dockerfile .
```

(3) Test that the docker image works on a small example dataset and push it to TIRA:

```
tira-cli verify-installation
tira-cli code-submission --path {% verbatim %}${{ inputs.directory }}{% endverbatim %} --task {{ task_id }} --dataset {{ input_dataset }}
```

