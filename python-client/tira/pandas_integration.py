class PandasIntegration():
    def __init__(self, tira_client):
        self.tira_client = tira_client

    def from_retriever_submission(self, approach, dataset, previous_stage=None, datasets=None):
        import pandas as pd
        from tira.ir_datasets_util import translate_irds_id_to_tirex
        task, team, software = approach.split('/')

        if dataset and datasets:
            raise ValueError(f'You can not pass both, dataset and datasets. Got dataset = {dataset} and datasets= {datasets}')

        if not datasets:
            datasets = [dataset]

        df_ret = []
        for dataset in datasets:
            ret, run_id = self.tira_client.download_run(task, translate_irds_id_to_tirex(dataset), software, team, previous_stage, return_metadata=True)
            ret['qid'] = ret['query'].astype(str)
            ret['docno'] = ret['docid'].astype(str)
            del ret['query']
            del ret['docid']

            ret['tira_task'] = task
            ret['tira_dataset'] = dataset
            ret['tira_first_stage_run_id'] = run_id
            df_ret += [ret]

        return pd.concat(df_ret)

    def transform_queries(self, approach, dataset, file_selection=('/q*.jsonl', '/q*.jsonl.gz')):
        import pandas as pd
        from glob import glob
        from tira.ir_datasets_util import translate_irds_id_to_tirex
        glob_entry = self.tira_client.get_run_output(approach, translate_irds_id_to_tirex(dataset)) + file_selection
        matching_files = glob(glob_entry)
        if len(matching_files) == 0:
            raise ValueError(f'Could not find a matching query output. Found: {matching_files}. Please specify the file_selection to resolve this.')

        ret = pd.read_json(matching_files[0], lines=True, dtype={'qid': str, 'query': str, 'query_id': str})
        if 'qid' not in ret and 'query_id' in ret:
            ret['qid'] = ret['query_id']
            del ret['query_id']

        return ret

    def transform_documents(self, approach, dataset, file_selection=('/d*.jsonl', '/d*.jsonl.gz')):
        import pandas as pd
        from glob import glob
        from tira.ir_datasets_util import translate_irds_id_to_tirex
        glob_entry = self.tira_client.get_run_output(approach, translate_irds_id_to_tirex(dataset)) + file_selection
        matching_files = glob(glob_entry)
        if len(matching_files) == 0:
            raise ValueError('Could not find a matching document output. Found: ' + matching_files + '. Please specify the file_selection to resolve this.')

        return pd.read_json(matching_files[0], lines=True)
