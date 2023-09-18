from tira.local_execution_integration import LocalExecutionIntegration


def test_non_existing_notebook_1():
    notebook = 'does-not-exist'

    actual = LocalExecutionIntegration().export_submission_from_jupyter_notebook(notebook)

    assert actual is None


def test_non_existing_notebook_2():
    notebook = 'does-not-exist/1/does-not-exist.ipynb'

    actual = LocalExecutionIntegration().export_submission_from_jupyter_notebook(notebook)

    assert actual is None


def test_notebook_submission_without_previous_stages():
    notebook = 'tests/resources/pyterrier-notebook-without-previous-stages.ipynb'

    expected = 'TIRA_COMMAND=/workspace/run-pyterrier-notebook.py --input ${TIRA_INPUT_DIRECTORY} --output ${TIRA_OUTPUT_DIRECTORY} --notebook /workspace/pyterrier-notebook-without-previous-stages.ipynb'
    actual = LocalExecutionIntegration().export_submission_from_jupyter_notebook(notebook)

    assert expected == actual

