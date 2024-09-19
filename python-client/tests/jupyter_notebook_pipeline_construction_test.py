import unittest
from pathlib import Path

from tira.local_execution_integration import LocalExecutionIntegration as Client
from tira.third_party_integrations import (
    extract_previous_stages_from_docker_image,
    extract_previous_stages_from_notebook,
    extract_to_be_executed_notebook_from_command_or_none,
    parse_ast_extract_assignment,
    parse_extraction_of_tira_approach,
    parse_extraction_of_tira_approach_bash,
)

TEST_DIR = Path(__file__).parent.resolve()


def build_docker_image(image):
    Client()._LocalExecutionIntegration__docker_client().images.build(
        path=".", dockerfile="tests/resources/" + image, tag=image
    )


class JupyterNotebookPipelineConstructionTest(unittest.TestCase):
    def test_no_notebook_is_extracted_for_none_command(self):
        command = None
        actual = extract_to_be_executed_notebook_from_command_or_none(command)

        self.assertIsNone(actual)

    def test_no_notebook_is_extracted_for_empty_command(self):
        command = ""
        actual = extract_to_be_executed_notebook_from_command_or_none(command)

        self.assertIsNone(actual)

    def test_notebook_is_extracted_for_pyterrier_command(self):
        expected = "/workspace/notebook.ipynb"
        command = (
            "/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook"
            " /workspace/notebook.ipynb"
        )

        actual = extract_to_be_executed_notebook_from_command_or_none(command)

        self.assertEqual(expected, actual)

    def test_notebook_is_extracted_when_subshell_is_available(self):
        expected = "/re-rank-with-tiny-bert.ipynb"
        command = (
            'bash -c export MODEL="$(huggingface-cli download $MODEL)" && /run-notebook.py --notebook'
            " /re-rank-with-tiny-bert.ipynb"
        )

        actual = extract_to_be_executed_notebook_from_command_or_none(command)

        self.assertEqual(expected, actual)

    def test_notebook_is_extracted_for_command_in_between(self):
        expected = "/notebook.ipynb"
        command = "/workspace/run-notebook.py --notebook /notebook.ipynb --input $inputDataset --output $outputDir"

        actual = extract_to_be_executed_notebook_from_command_or_none(command)

        self.assertEqual(expected, actual)

    def test_py_file_is_extracted_for_command_in_between(self):
        expected = "app.py"
        command = "python3 app.py"

        actual = extract_to_be_executed_notebook_from_command_or_none(command)

        self.assertEqual(expected, actual)

    def test_no_previous_stages_are_extracted_from_notebook_without_previous_stages(self):
        notebook = TEST_DIR / "resources" / "pyterrier-notebook-without-previous-stages.ipynb"
        expected = []

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_no_previous_stages_are_extracted_from_python_file_without_previous_stages(self):
        notebook = TEST_DIR / "resources" / "pyterrier-notebook-without-previous-stages.py"
        expected = []

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_pyterrier_index_as_previous_stage(self):
        notebook = TEST_DIR / "resources" / "retrieve-with-pyterrier-index.ipynb"
        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_for_query_transformation_01(self):
        python_line = (
            "gpt_sq_zs = tira.pt.transform_queries('ir-benchmarks/tu-dresden-03/qe-gpt3.5-sq-zs', dataset,"
            " prefix='llm_expansion_')"
        )
        expected = "ir-benchmarks/tu-dresden-03/qe-gpt3.5-sq-zs"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_for_document_transformation_01(self):
        python_line = (
            "document_entity_recognition = tira.pt.transform_documents('ir-lab-sose-2024/ir-nfmj/entity-recognition',"
            " pt_dataset)"
        )
        expected = "ir-lab-sose-2024/ir-nfmj/entity-recognition"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_llm_expansions_as_previous_stage(self):
        notebook = TEST_DIR / "resources" / "jupyter-notebook-with-query-expansion.ipynb"
        expected = [
            "ir-lab-sose-2024/tira-ir-starter/Index (tira-ir-starter-pyterrier)",
            "ir-benchmarks/tu-dresden-03/qe-gpt3.5-sq-zs",
        ]

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_pyterrier_index_as_previous_stage_for_python_file(self):
        notebook = TEST_DIR / "resources" / "retrieve-with-pyterrier-index.py"
        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_pyterrier_index_as_previous_stage_for_python_file_with_utility_function(self):
        python_line = (
            '    index = tira.pt.index("ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)", pt_dataset)'
        )
        expected = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_pyterrier_index_as_previous_stage_for_python_file_with_utility_function_complete(self):
        notebook = TEST_DIR / "resources" / "corpus-graph-with-pyterrier-index.py"
        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_parsing_of_ast_assignment_none(self):
        python_line = None
        k, v = parse_ast_extract_assignment(python_line)

        self.assertIsNone(k)
        self.assertIsNone(v)

    def test_parsing_of_ast_assignment_empty_string(self):
        python_line = None
        k, v = parse_ast_extract_assignment(python_line)

        self.assertIsNone(k)
        self.assertIsNone(v)

    def test_parsing_of_ast_assignment_method_call(self):
        python_line = (
            "index = tira.pt.index('ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)',"
            " 'longeval-tiny-train-20240315-training')"
        )
        k, v = parse_ast_extract_assignment(python_line)

        self.assertIsNone(k)
        self.assertIsNone(v)

    def test_parsing_of_ast_assignment_to_constant(self):
        python_line = "index = 3"
        expected_k, expeced_v = "index", 3
        k, v = parse_ast_extract_assignment(python_line)

        self.assertEqual(expected_k, k)
        self.assertEqual(expeced_v, v)

    def test_extraction_of_approach_is_failsave_01(self):
        python_line = "index = None"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_is_failsave_02(self):
        python_line = ""
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_is_failsave_03(self):
        python_line = None
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_is_failsave_04(self):
        python_line = "#index = tira.pt.index('tmp', 'longeval-tiny-train-20240315-training') # some comment"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_01(self):
        python_line = (
            "index = tira.pt.index('ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)',"
            " 'longeval-tiny-train-20240315-training')"
        )
        expected = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_02(self):
        python_line = "index = tira.pt.index('tmp', 'longeval-tiny-train-20240315-training') # some comment"
        expected = "tmp"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_03(self):
        python_line = 'index = tira.pt.index("tmp\'\\"a","longeval-tiny-train-20240315-training") # some comment'
        expected = "tmp'\"a"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_integration_against_docker_image_01(self):
        image = "mam10eks/bash-with-notebooks:latest"
        command = (
            "bash /workspace/run-notebook.sh --notebook /pyterrier-notebook-without-previous-stages.ipynb --input"
            " $inputDataset --output $outputDir"
        )

        expected = []
        actual = extract_previous_stages_from_docker_image(image, command)

        self.assertEqual(expected, actual)

    def test_integration_against_docker_image_02(self):
        image = "mam10eks/bash-with-notebooks:latest"
        command = (
            "bash /workspace/run-notebook.sh  --input $inputDataset --output $outputDir --notebook"
            " /pyterrier-notebook-without-previous-stages.ipynb"
        )

        expected = []
        actual = extract_previous_stages_from_docker_image(image, command)

        self.assertEqual(expected, actual)

    def test_integration_against_docker_image_03(self):
        image = "mam10eks/bash-with-notebooks:latest"
        command = (
            "bash /workspace/run-notebook.sh  --input $inputDataset --output $outputDir --notebook"
            " /retrieve-with-pyterrier-index.ipynb"
        )

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(image, command)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_from_bash_line_non_valid_input_01(self):
        bash_line = ""
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_from_bash_line_non_valid_input_02(self):
        bash_line = None
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_from_bash_line_non_valid_input_03(self):
        bash_line = "tira-cli --help"
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertIsNone(actual)

    def test_extraction_of_approach_from_bash_line_01(self):
        bash_line = (
            "INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach tmp) # some comment"
        )
        expected = "tmp"
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_from_bash_line_02(self):
        bash_line = (
            "INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach"
            " 'ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)') # some comment"
        )
        expected = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_from_bash_line_03(self):
        bash_line = (
            'INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach "tmp") # some comment'
        )
        expected = "tmp"
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_from_bash_line_04(self):
        bash_line = (
            "INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach"
            ' "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)") # some comment'
        )
        expected = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertEqual(expected, actual)

    def test_extraction_of_approach_from_bash_line_05(self):
        bash_line = (
            "INDEX=$(tira-cli download --dataset longeval-tiny-train-20240315-training --approach 'tmp') # some comment"
        )
        expected = "tmp"
        actual = parse_extraction_of_tira_approach_bash(bash_line)

        self.assertEqual(expected, actual)

    def test_pyterrier_index_as_previous_stage_for_bash_file(self):
        notebook = TEST_DIR / "resources" / "retrieve-with-pyterrier-bash.sh"
        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_no_previous_stage_for_bash_file(self):
        notebook = TEST_DIR / "resources" / "retrieve-no-previous-stages-bash.sh"
        expected = []

        actual = extract_previous_stages_from_notebook(notebook)

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_01(self):
        image = "dockerfile_bash_script_absolute"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(image, "/usr/bin/retrieve-with-pyterrier-bash.sh")

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_02(self):
        image = "dockerfile_bash_script_absolute"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(image)

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_03(self):
        image = "dockerfile_bash_script_absolute"
        build_docker_image(image)

        expected = []
        actual = extract_previous_stages_from_docker_image(image, "/etc/hostname")

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_04(self):
        image = "jupyter_script_relative"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(image)

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_05(self):
        image = "jupyter_script_relative"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(image, "python3 /usr/bin/retrieve-with-pyterrier-index.py")

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_06(self):
        image = "jupyter_script_relative"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(
            image, "python3 /usr/bin/retrieve-with-pyterrier-index.py; sleep3"
        )

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_07(self):
        image = "jupyter_script_relative"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(
            image, "python3 /usr/bin/retrieve-with-pyterrier-index.py&&sleep3"
        )

        self.assertEqual(expected, actual)

    def test_integration_against_custom_docker_image_08(self):
        image = "jupyter_script_relative"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(
            image, 'python3 "/usr/bin/retrieve-with-pyterrier-index.py"&&sleep3'
        )

        self.assertEqual(expected, actual)
        self.assertEqual(
            '"/usr/bin/retrieve-with-pyterrier-index.py"',
            extract_to_be_executed_notebook_from_command_or_none(
                'python3 "/usr/bin/retrieve-with-pyterrier-index.py"&&sleep3'
            ),
        )

    def test_integration_against_custom_docker_image_09(self):
        image = "jupyter_script_relative"
        build_docker_image(image)

        expected = ["ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"]
        actual = extract_previous_stages_from_docker_image(
            image, "python3 '/usr/bin/retrieve-with-pyterrier-index.py'&&sleep3"
        )

        self.assertEqual(expected, actual)
        self.assertEqual(
            "'/usr/bin/retrieve-with-pyterrier-index.py'",
            extract_to_be_executed_notebook_from_command_or_none(
                "python3 '/usr/bin/retrieve-with-pyterrier-index.py'&&sleep3"
            ),
        )

    def test_pyterrier_from_submission_with_percent_operator_01(self):
        python_line = (
            "        bm25_raw = tira.pt.from_submission('ir-benchmarks/tira-ir-starter/BM25"
            " (tira-ir-starter-pyterrier)', args.input_dataset) % args.first_stage_top_k"
        )
        expected = "ir-benchmarks/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_pyterrier_from_submission_with_percent_operator_02(self):
        notebook = TEST_DIR / "resources" / "keyquery-script.py"
        expected = []

        actual = extract_previous_stages_from_notebook(notebook)
        expected = [
            "ir-benchmarks/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)",
            "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)",
            "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)",
        ]

        self.assertEqual(expected, actual)

    def test_pyterrier_from_run_output_01(self):
        python_line = (
            "        bm25_raw = tira.get_run_output('ir-benchmarks/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)',"
            " args.input_dataset)"
        )
        expected = "ir-benchmarks/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)

    def test_pyterrier_from_run_output_02(self):
        python_line = (
            "        plaid_index = tira.get_run_output('reneuir-2024/reneuir-baselines/plaid-x', dataset_id) + '/index'"
        )
        expected = "reneuir-2024/reneuir-baselines/plaid-x"
        actual = parse_extraction_of_tira_approach(python_line)

        self.assertEqual(expected, actual)
