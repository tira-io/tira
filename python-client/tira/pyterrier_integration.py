class PyTerrierIntegration():
    def __init__(self, tira_client):
        self.tira_client = tira_client
        self.pd = tira_client.pd
        self.irds_docker_image = 'webis/tira-application:0.0.36'

    def retriever(self, approach, dataset=None):
        from tira.pyterrier_util import TiraFullRankTransformer
        input_dir = self.ensure_dataset_is_cached(dataset, dataset)
        return TiraFullRankTransformer(approach, self.tira_client, input_dir)

    def ensure_dataset_is_cached(self, irds_dataset_id, dataset):
        import os
        from pathlib import Path
        from tira.io_utils import run_cmd
        
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
                 self.irds_docker_image,
                 '--output_dataset_path', '/output',
                 '--ir_datasets_id', irds_dataset_id,
                 '--output_dataset_truth_path', '/truth'
                 ])

        return full_rank_data      

    def create_rerank_file(self, run_df=None, run_file=None, irds_dataset_id=None):
        from pathlib import Path
        import tempfile
        from tira.io_utils import run_cmd
        import gzip
        import json
        from tira.third_party_integrations import persist_and_normalize_run

        if run_df is None and run_file is None:
            raise ValueError('Please pass either run_df or run_file')

        if run_file is not None:
            return run_file

        run_file = tempfile.TemporaryDirectory('-rerank-run').name
        Path(run_file).mkdir(parents=True, exist_ok=True)

        if 'text' not in run_df.columns and 'body' not in run_df.columns:
            if not irds_dataset_id:
                raise ValueError(f'Please pass a irds_dataset_id. Got {irds_dataset_id}.')
            persist_and_normalize_run(run_df, 'system-is-ignored', run_file)

            cache_dir = self.tira_client.tira_cache_dir + '/pyterrier/' + irds_dataset_id
            irds_cache = cache_dir + '/irds-cache/'

            run_cmd(['docker', 'run',
                     '-v', irds_cache + ':/root/.ir_datasets/:rw',
                     '-v', run_file + ':/output/:rw',
                     '--entrypoint', '/irds_cli.sh',
                     self.irds_docker_image,
                     '--output_dataset_path', '/output',
                     '--ir_datasets_id', irds_dataset_id,
                     '--rerank', '/output'
            ])
        else:
            with gzip.open(run_file + '/rerank.jsonl.gz', 'wt') as f:
                for _, i in run_df.iterrows():
                    i = i.to_dict()

                    for k in ['original_query', 'original_document']:
                        if k not in i:
                            i[k] = {}

                    if 'text' not in i and 'body' in i:
                        i['text'] = i['body']

                    if 'text' not in i:
                        raise ValueError(f'I expect a field "text", but only found fields {i.keys()}.')

                    f.write(json.dumps(i) + '\n')

        return run_file

    def from_submission(self, approach, dataset=None, datasets=None):
        software = self.tira_client.docker_software(approach)
        if software.get('ir_re_ranker', False):
            return self.from_retriever_submission(approach, dataset, datasets=datasets)
        else:
            from tira.pyterrier_util import TiraRerankingTransformer
            return TiraRerankingTransformer(approach, self.tira_client, dataset, datasets)

    def from_retriever_submission(self, approach, dataset, previous_stage=None, datasets=None):
        import pyterrier as pt
        ret = self.pd.from_retriever_submission(approach, dataset, previous_stage, datasets)

        return pt.Transformer.from_df(ret)

    def transform_queries(self, approach, dataset, file_selection=('/*.jsonl', '/*.jsonl.gz')):
        from pyterrier.apply import generic
        ret = self.pd.transform_queries(approach, dataset, file_selection)
        cols = [i for i in ret.columns if i not in ['qid']]
        ret = {str(i['qid']): i for _, i in ret.iterrows()}

        def __transform_df(df):
            for col in cols:
                df[col] = df['qid'].apply(lambda i: ret[str(i)][col])
            return df

        return generic(__transform_df)

    def transform_documents(self, approach, dataset, file_selection=('/*.jsonl', '/*.jsonl.gz')):
        from pyterrier.apply import generic
        ret = self.pd.transform_documents(approach, dataset, file_selection)
        cols = [i for i in ret.columns if i not in ['docno']]
        ret = {str(i['docno']): i for _, i in ret.iterrows()}

        def __transform_df(df):
            for col in cols:
                df[col] = df['docno'].apply(lambda i: ret[str(i)][col])
            return df

        return generic(__transform_df)

    def reranker(self, approach, irds_id=None):
        from tira.pyterrier_util import TiraLocalExecutionRerankingTransformer
        return TiraLocalExecutionRerankingTransformer(approach, self.tira_client, irds_id=irds_id)

