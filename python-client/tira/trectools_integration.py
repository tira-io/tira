from pathlib import Path

from tira.ir_datasets_util import translate_irds_id_to_tirex


class TrecToolsIntegration:
    def __init__(self, tira_client):
        self.tira_client = tira_client
        self.pd = tira_client.pd

    def from_submission(self, approach, dataset):
        from trectools import TrecRun

        ret = self.tira_client.get_run_output(approach, translate_irds_id_to_tirex(dataset))

        return TrecRun(Path(ret) / "run.txt")
