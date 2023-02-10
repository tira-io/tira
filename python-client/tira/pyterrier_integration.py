class PyTerrierIntegration():
    def __init__(self, tira_client):
        self.tira_client = tira_client

    def retriever(self, approach, dataset=None):
        pass

    def from_submission(self, approach, dataset=None):
        software = self.tira_client.docker_software(approach)
        
        if not 'ir_re_ranker' in software or not software['ir_re_ranker']:
            return from_retriever_submission(approch, dataset)
        else:
            from tira.pyterrier_util import TiraRerankingTransformer
            
            return TiraRerankingTransformer(approach, self.tira_client)

    def from_retriever_submission(self, approach, dataset):
        import pyterrier as pt
        task, team, software = approach.split('/')

        if previous_stage and type(previous_stage) != str:
            previous_stage = previous_stage.name

        ret, run_id = tira.download_run(task, dataset, software, team, None, return_metadata=True)
        ret['qid'] = ret['query'].astype(str)
        ret['docid'] = ret['docid'].astype(str)
        del ret['query']
        del ret['docid']

        ret['tira_task'] = task
        ret['tira_dataset'] = dataset
        ret['tira_first_stage_run_id'] = run_id

        return pt.Transformer.from_df(ret)

    def reranker(self, approach):
        pass

