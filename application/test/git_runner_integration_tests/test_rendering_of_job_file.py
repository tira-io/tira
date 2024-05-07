from django.test import TestCase
from tira.git_runner_integration import GitRunner
from pathlib import Path


class TestRenderingOfJobFile(TestCase):
    def test_git_runner_can_be_instantiated(self):
        git_runner = GitRunner()

        self.assertIsNotNone(git_runner)

    def test_rendering_without_input_run(self):
        args = {'tira_software_id': '1', 'resources': 'small-resources', 'input_run': None}
        self.verify_metadata(args, 'test_rendering_without_input_run')

    def test_rendering_with_single_input_run(self):
        input_run = {'vm_id': 'some-vm-1', 'dataset_id': 'd1', 'run_id': 'r1'}
        args = {'tira_software_id': '1', 'resources': 'small-resources', 'input_run': input_run}
        self.verify_metadata(args, 'test_rendering_with_single_input_run')

    def test_rendering_with_multiple_input_runs(self):
        input_run = [
            {'vm_id': 'vm1', 'dataset_id': 'd1', 'run_id': 'r1'},
            {'vm_id': 'vm2', 'dataset_id': 'd1', 'run_id': 'r2'},
            {'vm_id': 'vm3', 'dataset_id': 'd1', 'run_id': 'r3'}
        ]
        args = {'tira_software_id': '1', 'resources': 'small-resources', 'input_run': input_run}
        self.verify_metadata(args, 'test_rendering_with_multiple_input_runs')

    def test_rendering_with_multiple_input_runs_and_hf_mounts(self):
        input_run = [
            {'vm_id': 'vm1', 'dataset_id': 'd1', 'run_id': 'r1'},
            {'vm_id': 'vm2', 'dataset_id': 'd1', 'run_id': 'r2'},
            {'vm_id': 'vm3', 'dataset_id': 'd1', 'run_id': 'r3'}
        ]
        args = {'tira_software_id': '1', 'resources': 'small-resources', 'input_run': input_run, 'mount_hf_model': 'a b c'}
        self.verify_metadata(args, 'test_rendering_with_multiple_input_runs_and_hf_mounts')

    def test_rendering_with_multiple_input_runs_and_hf_mounts_and_tira_image_workdir(self):
        input_run = [
            {'vm_id': 'vm1', 'dataset_id': 'd1', 'run_id': 'r1'},
            {'vm_id': 'vm2', 'dataset_id': 'd1', 'run_id': 'r2'},
            {'vm_id': 'vm3', 'dataset_id': 'd1', 'run_id': 'r3'}
        ]
        args = {'tira_software_id': '1', 'resources': 'small-resources', 'input_run': input_run, 'mount_hf_model': 'a b c', 'tira_image_workdir': '/tmp/a-b-c-d'}
        self.verify_metadata(args, 'test_rendering_with_multiple_input_runs_and_hf_mounts_and_tira_image_workdir')

    @staticmethod
    def verify_metadata(args, test_name):
        from approvaltests import verify
        from approvaltests.core.options import Options
        from approvaltests.namer.cli_namer import CliNamer
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            git_runner = GitRunner()
            git_runner.write_metadata_for_ci_job_to_repository(
                temp_dir, args.get('task_id', 'task_id'), args.get('transaction_id', 'transaction_id'),
                args.get('dataset_id', 'dataset_id'), args.get('vm_id', 'vm_id'), args.get('run_id', 'run_id'),
                args.get('identifier', 'identifier'), args.get('git_runner_image', 'Some image for the git runner'),
                args.get('git_runner_command', 'command in the git runner'), args.get('evaluator_id', 'evaluator_id'),
                args.get('user_image_to_execute', 'docker image specified by user'),
                args.get('user_command_to_execute', 'command in the git runner specified by the user'),
                args['tira_software_id'], args['resources'], args['input_run'], args.get('mount_hf_model', None), args.get('tira_image_workdir', None))

            job_file = Path(temp_dir) / args.get('dataset_id', 'dataset_id') / args.get('vm_id', 'vm_id') / \
                       args.get('run_id', 'run_id') / 'job-to-execute.txt'
            actual = open(job_file, 'r').read().strip()

        verify(actual, options=Options().with_namer(CliNamer(test_name)))
