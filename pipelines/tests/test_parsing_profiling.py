import unittest
import tempfile
from shutil import copytree
import importlib
import os

spec = importlib.util.spec_from_file_location('tira-persist-software-result', 'src/python/tira-persist-software-result.py')
process_profiling_logs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(process_profiling_logs)
parse_profiling_logs = process_profiling_logs.parse_profiling_logs
process_profiling_logs = process_profiling_logs.process_profiling_logs

class ParsingProfiling(unittest.TestCase):
    def test_data_structure(self):
        expected_files = ['output', 'profiling.zip', 'parsed_profiling.jsonl']
        target_dir = tempfile.NamedTemporaryFile().name + '-output/'
        copytree('tests/resources/profiling/', target_dir + '/output/profiling/')
        process_profiling_logs(target_dir + '/output')
        
        actual_files = os.listdir(target_dir)
        self.assertEqual(expected_files, actual_files)

    def test_parsing_of_gpu_utilization(self):
        expected = [
            {'timestamp': 0.0, 'key': 'gpu_utilization', 'value': '0 %'}, 
            {'timestamp': 3.0, 'key': 'gpu_utilization', 'value': '0 %'}, 
            {'timestamp': 6.0, 'key': 'gpu_utilization', 'value': '0 %'}
        ]
        actual = parse_profiling_logs('tests/resources/profiling/')
        actual = [i for i in actual if i['key'] == 'gpu_utilization'][:3]

        self.assertEqual(expected, actual)

    def test_parsing_of_ps_rss(self):
        expected = [
            {'timestamp': 0.0, 'key': 'ps_rss', 'value': 33420.0}, 
            {'timestamp': 3.0, 'key': 'ps_rss', 'value': 49800.0}, 
            {'timestamp': 6.0, 'key': 'ps_rss', 'value': 49800.0}
        ]
        actual = parse_profiling_logs('tests/resources/profiling/')
        actual = [i for i in actual if i['key'] == 'ps_rss'][:3]

        self.assertEqual(expected, actual)

    def test_parsing_of_ps_vsz(self):
        expected = [
            {'timestamp': 0.0, 'key': 'ps_vsz', 'value': 54412.0}, 
            {'timestamp': 3.0, 'key': 'ps_vsz', 'value': 71396.0}, 
            {'timestamp': 6.0, 'key': 'ps_vsz', 'value': 71396.0}
        ]
        actual = parse_profiling_logs('tests/resources/profiling/')
        actual = [i for i in actual if i['key'] == 'ps_vsz'][:3]

        self.assertEqual(expected, actual)

    def test_parsing_of_ps_cpu(self):
        expected = [
            {'timestamp': 0.0, 'key': 'ps_cpu', 'value': 0.1}, 
            {'timestamp': 3.0, 'key': 'ps_cpu', 'value': 13.6}, 
            {'timestamp': 6.0, 'key': 'ps_cpu', 'value': 6.8}
        ]
        actual = parse_profiling_logs('tests/resources/profiling/')
        actual = [i for i in actual if i['key'] == 'ps_cpu'][:3]

        self.assertEqual(expected, actual)

    def test_parsing_of_gpu_memory_used(self):
        expected = [
            {'timestamp': 0.0, 'key': 'gpu_memory_used', 'value': '1 MiB'}, 
            {'timestamp': 3.0, 'key': 'gpu_memory_used', 'value': '1 MiB'}, 
            {'timestamp': 6.0, 'key': 'gpu_memory_used', 'value': '1 MiB'}
        ]
        actual = parse_profiling_logs('tests/resources/profiling/')
        actual = [i for i in actual if i['key'] == 'gpu_memory_used'][:3]

        self.assertEqual(expected, actual)

    def test_parsing_of_profiling_for_non_profiling_directory(self):
        expected = []
        actual = parse_profiling_logs('tests/resources/')

        self.assertEqual(expected, actual)

