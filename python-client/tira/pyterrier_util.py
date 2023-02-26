from pyterrier.transformer import Transformer
import json
import pandas as pd
import tempfile
import gzip
import os


def merge_runs(topics, run_file):
    import numpy as np
    df = pd.read_csv(run_file, sep='\\s+', names=["qid", "q0", "docno", "rank", "score", "system"])
    df['qid'] = df['qid'].astype(str)
    df['docno'] = df['docno'].astype(str)
    topics['qid'] = topics['qid'].astype(str)

    common_columns = np.intersect1d(topics.columns, df.columns)
    join_on = ["qid", "docno"] if 'qid' in common_columns and 'docno' in common_columns else ['qid']

    # we drop columns in topics that exist in the df
    keeping = topics.columns
    drop_columns = [i for i in common_columns if i not in {"qid", "docno"}]
    if len(drop_columns) > 0:
        keeping = topics.columns[~ topics.columns.isin(drop_columns)]

    return topics[keeping].merge(df, how='left', left_on=join_on, right_on=join_on)


class TiraFullRankTransformer(Transformer):
    """
    A Transformer that re-executes some full-rank approach submitted to a shared task in TIRA.
    """

    def __init__(self, approach, tira_client, input_dir, verbose=False, **kwargs):
        self.approach = approach
        self.tira_client = tira_client
        self.input_dir = input_dir
        self.verbose = verbose

    def transform(self, topics):
        output_dir = tempfile.TemporaryDirectory('-pt-tira-local-execution-full-rank-transformer').name + '/output'
        os.makedirs(output_dir)

        self.tira_client.local_execution.run(identifier=self.approach,
            input_dir=self.input_dir, output_dir=output_dir,
            evaluate=False, verbose=self.verbose, dry_run=False
        )

        return merge_runs(topics, output_dir + '/run.txt')


class TiraRerankingTransformer(Transformer):
    """
    A Transformer that loads runs from TIRA that reranked some existing run.
    """

    def __init__(self, approach, tira_client, **kwargs):
        self.task, self.team, self.software = approach.split('/')
        self.tira_client = tira_client

    def transform(self, topics):
        import numpy as np
        assert "qid" in topics.columns
        if 'tira_task' not in topics.columns or 'tira_dataset' not in topics.columns or 'tira_first_stage_run_id' not in topics.columns:
            raise ValueError('This run needs to know the tira metadata: tira_task, tira_dataset, and tira_first_stage_run_id needs to be in the columns of the dataframe')

        tira_configurations = [json.loads(i) for i in topics[['tira_task', 'tira_dataset', 'tira_first_stage_run_id']].apply(lambda i: json.dumps(i.to_dict()), axis=1).unique()]
        df = []
        for tira_configuration in tira_configurations:
            df += [self.tira_client.download_run(tira_configuration['tira_task'], tira_configuration['tira_dataset'], self.software, self.team, tira_configuration['tira_first_stage_run_id'])]
        df = pd.concat(df)
        df['qid'] = df['query'].astype(str)
        df['docno'] = df['docid'].astype(str)
        del df['query']
        del df['docid']

        common_columns = np.intersect1d(topics.columns, df.columns)

        # we drop columns in topics that exist in the df
        keeping = topics.columns
        drop_columns = [i for i in common_columns if i not in {"qid", "docno"}]
        if len(drop_columns) > 0:
            keeping = topics.columns[~ topics.columns.isin(drop_columns)]

        return topics[keeping].merge(df, how='left', left_on=["qid", "docno"], right_on=["qid", "docno"])


class TiraLocalExecutionRerankingTransformer(Transformer):
    """
    A Transformer that re-execues software submitted in TIRA.
    """

    def __init__(self, approach, tira_client, verbose=False, irds_id=None, **kwargs):
        self.task, self.team, self.software = approach.split('/')
        self.approach = approach
        self.tira_client = tira_client
        self.verbose = verbose
        self.irds_id = irds_id

    def transform(self, topics):
        assert "qid" in topics.columns
        
        tmp_directory = tempfile.TemporaryDirectory('-pt-tira-local-execution-reranking-transformer').name
        input_dir = self.tira_client.pt.create_rerank_file(run_df=topics, irds_dataset_id=self.irds_id)
        output_dir = tmp_directory + '/output'
        os.makedirs(output_dir)

        self.tira_client.local_execution.run(identifier=self.approach,
            input_dir=input_dir, output_dir=output_dir,
            evaluate=False, verbose=self.verbose, dry_run=False
        )

        return merge_runs(topics, tmp_directory + '/output/run.txt')

