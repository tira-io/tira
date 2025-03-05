.. _ParticipatePage:

Participating in a Shared Task
==============================

.. note:: This tutorial assumes that you already created a user account. For the sake of the tutorial, we will create
    submissions for the ``ir-benchmarks`` task but it works the same for any other task.


.. _JoinTask:

Joining a Task and preparing your Environment
---------------------------------------------

To join a task, visit `tira.io/tasks <https://www.tira.io/tasks>`_, search for the task you would like to submit to,
and click its name to find the task's page.

Now you either have a button titled ``SUBMIT``, since you already
registered a group for this task, or it says ``REGISTER``. In the latter case, click on ``REGISTER``, fill out the form
that pops up appropriately, and confirm the registration by pressing ``Submit Registration``. After a reload, you should
see a ``SUBMIT`` button.

.. figure:: images/irbenchmarks_task_view.png
    :width: 300
    :align: center
    
    The task view for ``ir-benchmarks``. The ``REGISTER`` button could read ``SUBMIT``, if you are part of a group already.

Click on ``SUBMIT``. As you can see now, TIRA has three choices for submission (click on each respective tab to find
out more):

.. tab-set::

    .. tab-item:: Code Submission
        :sync: code-submission

        Code submission is the recommended form of submitting to TIRA. Code submissions are compatible with CI/CD systems like `Github Actions <https://github.com/features/actions>`_ and build a docker image from a git repository while collecting important experimental metadata to improve transparency and reproducibility.

        The requirements for code submissions are:

        (1) Your approach is in a git repository.
        (2) Your git repository is complete, i.e., contains all code and a Dockerfile to bundle the code.
        (3) Your git repository is clean.
            E.g., ``git status`` reports "nothing to commit, working tree clean".

        When those requirements are fulfilled, code submissions perform the following steps:

        (1) Build the docker image from the git repository while `tracking  important experimental meta data <https://github.com/tira-io/tirex-tracker>`_ (e.g., on git, code, etc.).
        (2) Run the docker image on a small spot check dataset to ensure it produces valid outputs.
        (3) Upload the docker image together with the meta data to TIRA.

    .. tab-item:: Docker Submission
        :sync: docker-submission

        .. todo:: TODO

    .. tab-item:: Run Upload
        :sync: upload-submission

        The upload submission is the simplest form of submitting and requires you to run the evaluation yourself and
        upload the :term:`runfile`. As such it has two notable drawbacks such that we discourage from using it:

        (1) Participants need access to the dataset. This may not be possible (e.g., due to legal reasons) or desirable
            (e.g., to avoid that future models profit from the author's analysis of the dataset).
        (2) The result is not verifiable -- the organizer can not ensure that your model actually produced the runfile.

.. hint:: If you want to use the simplest type of submission, we recommend a **Code Submission** as this works with Github Actions or other CI/CD automations.


.. _SubmitSubmission:

Submitting your Submission
--------------------------
At this point, you came up with a brilliant idea and would like to submit it to TIRA for evaluation and to take pride in
your leaderboard position.

(1) Optional: Uploading Artifacts (e.g., Hugging Face models required by your code)

(2) Submitting

    .. tab-set::

        .. tab-item:: Code Submission
            :sync: code-submission

            .. todo:: TODO

        .. tab-item:: Docker Submission
            :sync: docker-submission

            .. todo:: TODO

        .. tab-item:: Run Upload
            :sync: upload-submission

            .. todo:: TODO


.. todo:: For development: The "Country" field should probably be a dropdown

.. todo:: The upload of artifacts should not be inside the file-upload-submission since it indicates that it would not
    apply to docker- or code submissions, which it does.