import json
from pathlib import Path
from tira.tira_client import TiraClient
from datetime import datetime as dt
import zipfile



class ProfilingIntegration():
    """Access the profiling of runs executed in TIRA, e.g., CPU and memory usage, but als GPU utilization if available.
    """
    def __init__(self, tira_client: TiraClient):
        """Instantiate the ProfilingIntegration that uses the passed tira_client to acccess runs and parse their profiling metadata.

        Args:
            tira_client (TiraClient): the tira client to access the runs and their profiling metadata.
        """
        self.tira_client = tira_client
    
    def from_submission(self, approach: str, dataset: str, return_pd: bool=False, allow_without_evaluation: bool=False):
        """Return the profiling of the run identified by the approach on the dataset, i.e.,  CPU and memory usage, but als GPU utilization if available. Will throw an exception if no profiling data is available (e.g., if profiling was not configured for the task).

        Entries look like [{"timestamp": 0.0, "key": "ps_cpu", "value": 0.3}, ...]. The timestamp is the time in seconds since the start of the run, the key is the name of the metric, and the value is the value of the metric. The following metrics can be available (depending on the run and the system configuration):

        - elapsed_time: elapsed time in seconds since the start of the run until completion of the process.
        - ps_cpu: CPU usage in percent, produced by the `ps` command.
        - ps_rss: RSS Memory usage, produced by the `ps` command.
        - ps_vsz: VSZ Memory usage, produced by the `ps` command.
        - gpu_memory_used: Memory usage of the GPU in MiB, produced by the `nvidia-smi` command.
        - gpu_utilization: Utilization of the GPU in percent, produced by the `nvidia-smi` command.

        Args:
            approach (str): _description_
            dataset (str): The dataset identifier, e.g., "reneuir-2024/dl-top-1000-docs-20240701-training".
            return_pd (str, optional): Return as pandas DataFrame instead of as list of dictionaries. Defaults to False.
            allow_without_evaluation (_type_, optional): _description_. Defaults to False.
        """

        try:
            run_output_dir = self.tira_client.get_run_output(approach, dataset, allow_without_evaluation)
            run_output_dir = Path(run_output_dir).parent
        except Exception as e:
            raise Exception(f"No profiling data available for approach '{approach}' on dataset '{dataset}'. Could not load run", e)

        profiling_file = run_output_dir / "parsed_profiling.jsonl"
        start_time = run_output_dir / "start"
        end_time = run_output_dir / "end"
        profiling_zip = run_output_dir / "profiling.zip"

        if not profiling_file.exists() or ((not start_time.exists() or not end_time.exists()) and not profiling_zip.exists()):
            raise Exception(f"No profiling data available for approach '{approach}' on dataset '{dataset}'.")

        try:
            start_time = open(start_time).read()
            end_time = open(end_time).read()
        except:
            archive = zipfile.ZipFile(profiling_zip, 'r')
            start_time = archive.read('start').decode('utf-8')
            end_time = archive.read('end').decode('utf-8')

        start_time = ' '.join(start_time.split()[:4])
        end_time = ' '.join(end_time.split()[:4])
        start_time = dt.strptime(start_time, '%a %b %d %H:%M:%S').timestamp()
        end_time = dt.strptime(end_time, '%a %b %d %H:%M:%S').timestamp()
        ret = []
        with open(profiling_file, 'r') as f:
            for line in f:
                ret.append(json.loads(line))
        
        ret.append({"timestamp": end_time - start_time, "key": "elapsed_time", "value": end_time - start_time})

        if return_pd:
            import pandas as pd
            return pd.DataFrame(ret)
        else:
            return ret
