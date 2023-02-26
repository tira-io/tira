class PyTerrierIntegration():
    def __init__(self, tira_client):
        self.tira_client = tira_client

    def retriever(self, approach, dataset=None, verbose=False):
        from tira.pyterrier_util import TiraFullRankTransformer
        input_dir = self.ensure_dataset_is_cached(dataset, dataset)
        return TiraFullRankTransformer(approach, self.tira_client, input_dir, verbose)

    def ensure_dataset_is_cached(self, irds_dataset_id, dataset):
        import os
        from pathlib import Path
        from tira.io_utils import run_cmd
        import json

        cache_dir = self.tira_client.tira_cache_dir + '/pyterrier/' + irds_dataset_id
        full_rank_data = cache_dir + '/full-rank/'
        truth_data = cache_dir + '/truth-data/'
        irds_cache = cache_dir + '/irds-cache/'

        if os.path.isfile(full_rank_data + '/documents.jsonl'):
            return full_rank_data

        Path(full_rank_data).mkdir(parents=True, exist_ok=True)
        Path(truth_data).mkdir(parents=True, exist_ok=True)
        Path(irds_cache).mkdir(parents=True, exist_ok=True)

        run_cmd(['docker', 'run',
                 '-v', irds_cache + ':/root/.ir_datasets/:rw',
                 '-v', full_rank_data + ':/output/:rw',
                 '-v', truth_data + ':/truth/:rw',
                 '--entrypoint', '/irds_cli.sh',
                 'webis/tira-application:0.0.36',
                 '--output_dataset_path', '/output',
                 '--ir_datasets_id', irds_dataset_id,
                 '--output_dataset_truth_path', '/truth'
                 ])

        return full_rank_data      

    def from_submission(self, approach, dataset=None, datasets=None):
        software = self.tira_client.docker_software(approach)
        
        if not 'ir_re_ranker' in software or not software['ir_re_ranker']:
            return self.from_retriever_submission(approach, dataset, datasets=datasets)
        else:
            from tira.pyterrier_util import TiraRerankingTransformer
            
            return TiraRerankingTransformer(approach, self.tira_client)

    def from_retriever_submission(self, approach, dataset, previous_stage=None, datasets=None):
        import pyterrier as pt
        import pandas as pd
        task, team, software = approach.split('/')
        
        
        if dataset and datasets:
            raise ValueError(f'You can not pass both, dataset and datasets. Got dataset = {dataset} and datasets= {datasets}')
        
        if not datasets:
            datasets = [dataset]

        df_ret = []
        for dataset in datasets:
            ret, run_id = self.tira_client.download_run(task, dataset, software, team, previous_stage, return_metadata=True)
            ret['qid'] = ret['query'].astype(str)
            ret['docno'] = ret['docid'].astype(str)
            del ret['query']
            del ret['docid']

            ret['tira_task'] = task
            ret['tira_dataset'] = dataset
            ret['tira_first_stage_run_id'] = run_id
            df_ret += [ret]

        return pt.Transformer.from_df(pd.concat(df_ret))

    def reranker(self, approach):
        from tira.pyterrier_util import TiraLocalExecutionRerankingTransformer
        return TiraLocalExecutionRerankingTransformer(approach, self.tira_client)

