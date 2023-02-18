class PyTerrierIntegration():
    def __init__(self, tira_client):
        self.tira_client = tira_client

    def retriever(self, approach, dataset=None):
        pass

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
        pass

