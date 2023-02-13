from pyterrier.transformer import Transformer
from matchpy import Wildcard, Symbol, Operation, Arity
import json

class TiraRerankingTransformer(Transformer, Operation):
    """
    A Transformer that loads runs from TIRA that reranked some existing run.
    """
    arity = Arity.nullary

    def __init__(self, approach, tira_client, **kwargs):
        super().__init__(operands=[], **kwargs)
        self.operands=[]
        self.task, self.team, self.software = approach.split('/')
        self.tira_client = tira_client
        assert "qid" in self.df.columns

    def transform(self, topics):
        import numpy as np
        assert "qid" in topics.columns
        if 'tira_task' not in topics.columns or 'tira_dataset' not in columns or 'tira_first_stage_run_id':
            raise ValueError('This run needs to know the tira metadata: tira_task, tira_dataset, and tira_first_stage_run_id needs to be in the columns of the dataframe')

        tira_configurations = [json.loads(i) for i in topics[['tira_task', 'tira_dataset', 'tira_first_stage_run_id']].apply(lambda i: json.dumps(i)).unique()]
        df = []
        for tira_configuration in tira_configurations:
            df += [self.tira_client.download_run(tira_configuration['tira_task'], tira_configuration['tira_dataset'], self.software, self.team, tira_configuration['tira_first_stage_run_id'])]
        df = pd.concat(df)

        common_columns = np.intersect1d(topics.columns, self.df.columns)

        # we drop columns in self.df that exist in the topics
        self.df = df[[i for i in df.columns if i not in common_columns]]

        return topics.merge(self.df, on="qid")
